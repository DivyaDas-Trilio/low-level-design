"""Fine entity - represents penalties for overdue books"""

from datetime import datetime
from typing import Optional
import uuid

from ..exceptions import InvalidFineAmountError, InvalidReasonError, AlreadyPaidError
from ..value_objects import Money


class Fine:
    """Entity representing a fine/penalty for a member"""

    def __init__(self, member_id: str, amount: float, reason: str, fine_id: Optional[str] = None):
        # Entity identity
        self.fine_id = fine_id or str(uuid.uuid4())

        # Invariant: Fine amount must be positive
        if amount <= 0:
            raise InvalidFineAmountError("Fine amount must be positive")

        # Invariant: Reason cannot be empty
        if not reason.strip():
            raise InvalidReasonError("Fine reason cannot be empty")

        # Entity state
        self.member_id = member_id
        self.amount = Money(amount)
        self.reason = reason
        self.is_paid = False
        self.created_date = datetime.now()
        self.paid_date: Optional[datetime] = None

    def mark_as_paid(self) -> None:
        """Mark the fine as paid"""
        # Invariant: Cannot pay already paid fine
        if self.is_paid:
            raise AlreadyPaidError(f"Fine {self.fine_id} is already paid")

        self.is_paid = True
        self.paid_date = datetime.now()

    def is_overdue(self, days: int = 30) -> bool:
        """Check if fine is overdue (unpaid for given days)"""
        if self.is_paid:
            return False

        days_since_created = (datetime.now() - self.created_date).days
        return days_since_created > days

    def __str__(self):
        status = "PAID" if self.is_paid else "UNPAID"
        return f"Fine({self.fine_id}): {self.amount} - {self.reason} [{status}]"

    def __eq__(self, other):
        if not isinstance(other, Fine):
            return False
        return self.fine_id == other.fine_id