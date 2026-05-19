"""Loan entity - represents a borrowing transaction"""

from datetime import datetime, timedelta
from typing import Optional
import uuid

from ..exceptions import InvalidBorrowDateError, InvalidLoanPeriodError, LoanAlreadyReturnedError
from ..value_objects import LoanStatus, Money


class Loan:
    """Entity representing a loan/borrowing transaction"""

    def __init__(self, member_id: str, book_id: str, borrow_date: Optional[datetime] = None,
                 loan_period_days: int = 14, loan_id: Optional[str] = None):
        # Entity identity
        self.loan_id = loan_id or str(uuid.uuid4())

        # Invariant: Borrow date cannot be in future
        self.borrow_date = borrow_date or datetime.now()
        if self.borrow_date > datetime.now():
            raise InvalidBorrowDateError("Borrow date cannot be in the future")

        # Invariant: Loan period must be positive
        if loan_period_days <= 0:
            raise InvalidLoanPeriodError("Loan period must be positive")

        # Entity state
        self.member_id = member_id  # Reference to Member aggregate
        self.book_id = book_id      # Reference to Book aggregate
        self.loan_period_days = loan_period_days
        self.due_date = self.borrow_date + timedelta(days=loan_period_days)
        self.return_date: Optional[datetime] = None
        self.status = LoanStatus.ACTIVE

        # Fine calculation constants
        self.DAILY_FINE_RATE = 1.0  # $1 per day

    def return_book(self, return_date: Optional[datetime] = None) -> Money:
        """Mark loan as returned and calculate penalty if overdue"""
        # Invariant: Cannot return already returned book
        if self.status == LoanStatus.RETURNED:
            raise LoanAlreadyReturnedError(f"Loan {self.loan_id} has already been returned")

        self.return_date = return_date or datetime.now()
        self.status = LoanStatus.RETURNED

        # Calculate penalty for overdue return
        penalty = self.calculate_penalty()
        return penalty

    def calculate_penalty(self) -> Money:
        """Calculate penalty for overdue books"""
        if not self.is_overdue():
            return Money(0.0)

        # Calculate overdue days
        check_date = self.return_date or datetime.now()
        overdue_days = (check_date - self.due_date).days

        penalty_amount = overdue_days * self.DAILY_FINE_RATE
        return Money(penalty_amount)

    def is_overdue(self) -> bool:
        """Check if loan is currently overdue"""
        if self.status == LoanStatus.RETURNED:
            # Check if it was returned late
            return self.return_date > self.due_date

        # For active loans, check against current time
        return datetime.now() > self.due_date

    def get_overdue_days(self) -> int:
        """Get number of overdue days"""
        if not self.is_overdue():
            return 0

        check_date = self.return_date or datetime.now()
        return max(0, (check_date - self.due_date).days)

    def extend_loan(self, additional_days: int) -> None:
        """Extend the loan period (business rule: only for non-overdue loans)"""
        if self.status != LoanStatus.ACTIVE:
            raise ValueError("Cannot extend returned loan")

        if self.is_overdue():
            raise ValueError("Cannot extend overdue loan")

        if additional_days <= 0:
            raise ValueError("Extension days must be positive")

        self.due_date = self.due_date + timedelta(days=additional_days)

    def days_until_due(self) -> int:
        """Get number of days until due (negative if overdue)"""
        if self.status == LoanStatus.RETURNED:
            return 0

        days = (self.due_date - datetime.now()).days
        return days

    def get_status_description(self) -> str:
        """Get human-readable status"""
        if self.status == LoanStatus.RETURNED:
            return "Returned"
        elif self.is_overdue():
            return f"Overdue by {self.get_overdue_days()} days"
        else:
            days_left = self.days_until_due()
            return f"Due in {days_left} days"

    def __str__(self):
        return f"Loan({self.loan_id}): Member {self.member_id} -> Book {self.book_id} [{self.get_status_description()}]"

    def __eq__(self, other):
        if not isinstance(other, Loan):
            return False
        return self.loan_id == other.loan_id