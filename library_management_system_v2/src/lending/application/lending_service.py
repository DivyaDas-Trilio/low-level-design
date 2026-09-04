from datetime import date

from shared.ids import MemberId, CopyId, LoanId, FineId
from lending.domain.loan import Loan
from lending.domain.borrowing_service import BorrowingService
from lending.domain.repository import LoanRepository
# Cross-subdomain composition happens at the APPLICATION layer (allowed — the
# "no cross-subdomain imports" rule is a DOMAIN-layer rule). We reach the other
# subdomains only through their PUBLIC interfaces / application services.
from membership.domain.repository import IMembershipRepository
from catalog.domain.repository.book_copy_repo import BookCopyRepository
from fines.application.fine_service import FineService


class LendingService:
    """Application service for the Lending subdomain — orchestrates the borrow/return
    use cases across membership + catalog + lending + fines. Holds no business rules.
    """

    def __init__(self, members: IMembershipRepository, copies: BookCopyRepository,
                 loans: LoanRepository, borrowing: BorrowingService,
                 fines: FineService,                       # fines' PUBLIC app service (cross-subdomain)
                 clock=date.today):                        # injectable clock (testable time)
        self._members = members
        self._copies = copies
        self._loans = loans
        self._borrowing = borrowing
        self._fines = fines
        self._clock = clock

    # --- UC-1: borrow a book (member + copy + loan) ---
    def borrow_book(self, member_id: MemberId, copy_id: CopyId) -> LoanId:
        member = self._members.get(member_id)                       # LOAD (membership repo)
        copy   = self._copies.get(copy_id)                          # LOAD (catalog repo)
        active = self._loans.count_active_for_member(member.id)     # LOAD (lending repo → a count)

        self._borrowing.check_can_borrow(                           # DECIDE (domain service — VALUES)
            member_active=member.is_active, active_loan_count=active)

        copy.issue()                                                # MUTATE (catalog guards availability)
        loan = Loan.create(member.id, copy.copy_id, self._clock())  # MUTATE (lending factory)

        self._copies.save(copy)                                     # SAVE both aggregates
        self._loans.save(loan)
        return loan.id

    # --- UC-2 + UC-4: return a book; assess a fine if late ---
    def return_book(self, loan_id: LoanId) -> FineId | None:
        loan = self._loans.get(loan_id)                             # LOAD (lending)
        copy = self._copies.get(loan.copy_id)                       # LOAD (catalog)

        days_overdue = loan.return_copy(self._clock())              # DECIDE (lending: transition + FACT)
        copy.return_copy()                                          # MUTATE (catalog: back to AVAILABLE)

        self._loans.save(loan)                                      # SAVE both
        self._copies.save(copy)
        # fines OWNS fine creation — call its public app service with the FACT (cross-subdomain)
        return self._fines.assess_fine(loan.member_id, loan.id, days_overdue)

    # --- UC-5: list overdue loans ---
    def list_overdue(self, as_of: date | None = None) -> list[Loan]:
        return self._loans.find_overdue(as_of or self._clock())
