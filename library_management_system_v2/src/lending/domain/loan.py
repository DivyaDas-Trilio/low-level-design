from datetime import date

from shared.ids import LoanId, MemberId, CopyId
from lending.domain.daterange import DateRange
from lending.domain.enums import LoanStatus
from lending.domain.exceptions import LoanAlreadyReturnedError


class Loan:
    """A specific copy out to a member with a due date — the lending aggregate root.

    References the member and the copy BY ID (both separate aggregates). Reports
    `days_overdue` as a FACT; it never turns that into money (the fine Strategy does).
    """

    def __init__(self, loan_id: LoanId, member_id: MemberId, copy_id: CopyId,
                 period: DateRange, status: LoanStatus = LoanStatus.ACTIVE):
        self.id = loan_id
        self.member_id = member_id            # by-ID ref → Member (membership aggregate)
        self.copy_id = copy_id                # by-ID ref → BookCopy (catalog aggregate)
        self.period = period                  # DateRange VO (borrow..due)
        self._status = status

    # --- factory: encodes rule #2 (due = borrow + N days); guarantees I-3 at birth ---
    @classmethod
    def create(cls, member_id: MemberId, copy_id: CopyId,
               borrow_date: date, loan_days: int = 5) -> "Loan":
        period = DateRange.for_loan(borrow_date, loan_days)   # loan_days is a policy value
        return cls(LoanId.new(), member_id, copy_id, period)

    # --- identity: entities are equal BY ID ---
    def __eq__(self, other) -> bool:
        return isinstance(other, Loan) and self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)

    # --- queries (CQS): facts, no side effects ---
    @property
    def status(self) -> LoanStatus:
        return self._status

    @property
    def due_date(self) -> date:
        return self.period.end

    def is_overdue(self, as_of: date) -> bool:
        return self._status is not LoanStatus.RETURNED and self.period.is_overdue(as_of)

    def days_overdue(self, as_of: date) -> int:
        return self.period.days_overdue(as_of)              # the FACT (0 if on time)

    # --- commands (CQS): change state, return nothing (or the fact) ---
    def return_copy(self, on_date: date) -> int:
        if self._status is LoanStatus.RETURNED:
            raise LoanAlreadyReturnedError(str(self.id))    # I-8: no double-return
        days_overdue = self.period.days_overdue(on_date)    # compute the FACT before transitioning
        self._status = LoanStatus.RETURNED
        return days_overdue                                 # app service turns this into a fine

    def mark_overdue(self) -> None:
        if self._status is LoanStatus.ACTIVE:               # ACTIVE -> OVERDUE (for UC-5 batch)
            self._status = LoanStatus.OVERDUE
