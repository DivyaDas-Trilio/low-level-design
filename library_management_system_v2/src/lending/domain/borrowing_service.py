from lending.domain.exceptions import BorrowingLimitExceededError, MemberNotActiveError


class BorrowingService:
    """Borrowing policy: may a member take another loan?

    A DOMAIN SERVICE — it encodes a business rule (rule #4) whose data spans two
    aggregates (Member's active status + the Loan count), so it fits no single
    entity. Pure & stateless, and GIVEN plain values (never Member/BookCopy
    objects) so `lending` imports nothing from membership/catalog (Option 1).
    """

    def __init__(self, max_active_loans: int = 2):
        self._max_active_loans = max_active_loans          # rule #4 — configurable, not hard-coded

    def check_can_borrow(self, *, member_active: bool, active_loan_count: int) -> None:
        """Raise a DomainError if the borrow is disallowed; return normally if OK."""
        if not member_active:                              # a membership FACT, passed as a value
            raise MemberNotActiveError("member is blocked")
        if active_loan_count >= self._max_active_loans:    # the <= 2 rule (Loan aggregate)
            raise BorrowingLimitExceededError("borrowing limit reached")
        # NOTE: copy availability is the copy's OWN invariant — guarded by copy.issue().
