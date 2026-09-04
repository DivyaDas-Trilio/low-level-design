"""Composition root + demo harness — drives the use cases directly.

No web framework, no database: in-memory repos wired here, use cases called
directly. Run with:  python src/main.py
"""

from datetime import date

from shared.ids import MemberId
from shared.exceptions import DomainError, EntityAlreadyExistsError, EntityNotFoundError

from catalog.application.catalog_service import CatalogService
from catalog.infrastructure.inmemory_book_repo import InMemoryBookRepository
from catalog.infrastructure.inmemory_bookcopy_repo import InMemoryBookCopyRepository
from catalog.domain.exceptions import CopyNotAvailableError

from membership.application.membership_service import MembershipService
from membership.infrastructure.inmemory_membership_repository import InMemoryMembershipRepository

from lending.application.lending_service import LendingService
from lending.domain.borrowing_service import BorrowingService
from lending.infrastructure.inmemory_loan_repository import InMemoryLoanRepository
from lending.domain.exceptions import BorrowingLimitExceededError, MemberNotActiveError

from fines.application.fine_service import FineService
from fines.infrastructure.inmemory_fine_repository import InMemoryFineRepository
from fines.domain.fine_calculation import StandardFineStrategy
from fines.domain.money import Money

from config import settings            # 12-Factor III: config read at the edge, injected inward


class Clock:
    """A controllable clock (SystemClock in real code) — lets the demo advance 'today'."""

    def __init__(self, today: date | None = None):
        self._today = today or date.today()

    def __call__(self) -> date:
        return self._today

    def set(self, d: date) -> None:
        self._today = d


# ---------- composition root: ONE set of repos + services, shared ----------
def build_services():
    members = InMemoryMembershipRepository()
    books   = InMemoryBookRepository()
    copies  = InMemoryBookCopyRepository()
    loans   = InMemoryLoanRepository()
    fine_repo = InMemoryFineRepository()
    clock = Clock()

    catalog    = CatalogService(books, copies)
    membership = MembershipService(members)
    # policy from config: the fine rate and borrow limit are env-tunable, no rebuild
    fines      = FineService(fine_repo, StandardFineStrategy(Money(settings.fine_rate_paise)))
    lending    = LendingService(members, copies, loans,
                                BorrowingService(max_active_loans=settings.max_active_loans),
                                fines, clock)
    return catalog, membership, lending, fines, clock


# ---------- demos ----------
def demo_catalog(catalog: CatalogService) -> None:
    print("=== Catalog subdomain demo ===")
    book_id = catalog.add_book("978-0-13-468599-1", "Clean Code", "Robert Martin", "Tech")
    catalog.add_copy(book_id); catalog.add_copy(book_id); c3 = catalog.add_copy(book_id)
    print(f"UC-9  added book with 3 copies | available: {catalog.count_available(book_id)}")
    catalog.mark_copy_lost(c3)
    print(f"UC-8  marked 1 LOST -> available: {catalog.count_available(book_id)}")
    print(f"UC-7  search 'clean': {[b.title for b in catalog.search_books('clean')]}")
    catalog.update_book(book_id, title="Clean Code 2e")
    print(f"UC-9  updated title:  {catalog.search_books('clean')[0].title}")


def demo_membership(membership: MembershipService) -> None:
    print("\n=== Membership subdomain demo ===")
    try:
        membership.get_member(MemberId("does-not-exist"))
    except EntityNotFoundError:
        print("UC-10 get unknown -> EntityNotFoundError")

    mid = membership.register_member(name="Divya", email="divya.das@trilio.io")
    print(f"UC-10 registered {str(mid)[:8]} | active: {membership.get_member(mid).is_active}")

    try:
        membership.register_member(name="Divya2", email="Divya.Das@TRILIO.io")   # same email, diff case
    except EntityAlreadyExistsError:
        print("UC-10 duplicate email -> EntityAlreadyExistsError")

    membership.block_member(mid)
    print(f"UC-10 blocked   -> active: {membership.get_member(mid).is_active}")
    membership.unblock_member(mid)
    print(f"UC-10 unblocked -> active: {membership.get_member(mid).is_active}")

    membership.remove_member(mid)
    try:
        membership.get_member(mid)
    except EntityNotFoundError:
        print("UC-10 removed -> EntityNotFoundError on lookup")


def demo_borrow(catalog: CatalogService, membership: MembershipService,
                lending: LendingService) -> None:
    print("\n=== Lending: borrow (cross-subdomain) demo ===")
    alice = membership.register_member("Alice", "alice@example.com")           # membership
    bob   = membership.register_member("Bob", "bob@example.com")
    bid = catalog.add_book("978-0-13-235088-4", "Refactoring", "Martin Fowler")  # catalog
    c1 = catalog.add_copy(bid); c2 = catalog.add_copy(bid); c3 = catalog.add_copy(bid)
    print(f"seeded 2 members + 3 copies | available: {catalog.count_available(bid)}")

    loan1 = lending.borrow_book(alice, c1)                                     # UC-1
    print(f"UC-1  Alice borrowed c1 -> loan {str(loan1)[:8]} | available: {catalog.count_available(bid)}")
    lending.borrow_book(alice, c2)
    print(f"UC-1  Alice borrowed c2 | available: {catalog.count_available(bid)}")

    try:                                                                       # Bob (0 loans) tries loaned c1
        lending.borrow_book(bob, c1)
    except CopyNotAvailableError:
        print("UC-1  Bob borrows loaned c1 -> CopyNotAvailableError (copy.issue guard)")

    try:                                                                       # Alice's 3rd -> limit
        lending.borrow_book(alice, c3)
    except BorrowingLimitExceededError:
        print("UC-1  Alice 3rd borrow -> BorrowingLimitExceededError (<=2 rule)")

    membership.block_member(bob)                                               # blocked member
    try:
        lending.borrow_book(bob, c3)
    except MemberNotActiveError:
        print("UC-1  blocked Bob borrow -> MemberNotActiveError")


def demo_return(catalog: CatalogService, membership: MembershipService,
                lending: LendingService, fines: FineService, clock: Clock) -> None:
    print("\n=== Lending: return + fine (borrow -> late return -> fine -> pay) ===")
    clock.set(date(2026, 1, 1))                                                # borrow on Jan 1 (due Jan 6)
    mid = membership.register_member("Carol", "carol@example.com")
    bid = catalog.add_book("978-0-321-12521-7", "Domain-Driven Design", "Eric Evans")
    cid = catalog.add_copy(bid)
    loan_id = lending.borrow_book(mid, cid)
    print(f"borrowed on {clock()} -> loan {str(loan_id)[:8]} | available: {catalog.count_available(bid)}")

    clock.set(date(2026, 1, 9))                                                # return 3 days late
    fine_id = lending.return_book(loan_id)                                     # UC-2 + UC-4
    print(f"returned on {clock()} -> available: {catalog.count_available(bid)}")
    fine = fines.get_fine(fine_id)
    print(f"UC-4  fine: {fine.amount} ({fine.status.value}) | unpaid for Carol: {len(fines.list_unpaid_by_member(mid))}")

    fines.pay_fine(fine_id)                                                    # UC-6
    print(f"UC-6  paid -> status: {fines.get_fine(fine_id).status.value} | unpaid: {len(fines.list_unpaid_by_member(mid))}")


def main() -> None:
    catalog, membership, lending, fines, clock = build_services()   # shared repos + services
    try:
        demo_catalog(catalog)
        demo_membership(membership)
        demo_borrow(catalog, membership, lending)
        demo_return(catalog, membership, lending, fines, clock)
    except DomainError as e:                                          # handle at the edge, in ONE place
        print(f"Error: {type(e).__name__}: {e}")


if __name__ == "__main__":
    main()
