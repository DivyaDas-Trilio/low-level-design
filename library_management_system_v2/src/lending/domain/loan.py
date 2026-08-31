from lending.domain.exceptions import LoanAlreadyReturnedError
from lending.domain.enums import LoanStatus
from shared.ids import LoanId
from lending.domain.daterange import DateRange
from datetime import date

class Loan:
    def __init__(self, loan_id: LoanId, is_overdue: DateRange, start_date: date, due_date: date, **kwargs):
        self._id: LoanId = loan_id
        self._start_date = start_date
        self._is_overdue: bool = False
        self._days_overdue = None
        self._due_date: date = due_date
        self._status: LoanStatus = LoanStatus.ACTIVE

    @property
    def is_overdue(self):
        return self._is_overdue

    @property
    def days_overdue(self):
        self._days_overdue = DateRange.for_loan(self._start_date,
                                           5).days_overdue(date.today())
        return self._days_overdue

    @property
    def due_date(self):
        return self._days_overdue

    def create(self):
        ...

    def return_copy(self):
        if self._status in [LoanStatus.RETURNED]:
            raise LoanAlreadyReturnedError("LOan Already Returned.")

    def mark_overdue(self):
        ...
