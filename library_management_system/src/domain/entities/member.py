"""Member entity - aggregate root for member management"""

from datetime import datetime, timedelta
from typing import List, Optional
import uuid

from ..exceptions import InvalidEmailError, InvalidNameError, MemberCannotBorrowError
from ..value_objects import Email, LibraryCard, MemberType, Money
from .fine import Fine


class Member:
    """Aggregate root for Member with library card and fines"""

    def __init__(self, name: str, email: str, member_type: str = "REGULAR",
                 member_id: Optional[str] = None):
        # Entity identity
        self.member_id = member_id or str(uuid.uuid4())

        # Invariant: Name cannot be empty
        if not name.strip():
            raise InvalidNameError("Member name cannot be empty")

        # Invariant: Email must be valid (using value object)
        self.email = Email(email)

        # Entity state
        self.name = name.strip()
        self.member_type = MemberType(member_type)
        self.created_date = datetime.now()

        # Aggregate components (owned by Member)
        self.library_card = self._create_library_card()
        self.fines: List[Fine] = []

        # Track active loans by ID (references to Loan aggregate)
        self.active_loan_ids: List[str] = []

    def _create_library_card(self) -> LibraryCard:
        """Create library card when member is created"""
        issue_date = datetime.now()
        # Cards are valid for 2 years
        expiry_date = issue_date + timedelta(days=730)
        card_number = f"LIB{self.member_id[:8].upper()}"

        return LibraryCard(card_number, issue_date, expiry_date)

    def can_borrow_book(self) -> bool:
        """Business rule: Check if member can borrow more books"""
        # Invariant: Cannot borrow more than 5 books
        if len(self.active_loan_ids) >= 5:
            return False

        # Invariant: Cannot borrow if unpaid fines exist
        if self.get_total_unpaid_fines().amount > 0:
            return False

        # Invariant: Library card must be valid
        if not self.library_card.is_valid():
            return False

        return True

    def add_fine(self, amount: float, reason: str) -> Fine:
        """Add a fine to the member"""
        fine = Fine(self.member_id, amount, reason)
        self.fines.append(fine)
        return fine

    def pay_fine(self, fine_id: str) -> None:
        """Pay a specific fine"""
        fine = self._find_fine_by_id(fine_id)
        if not fine:
            raise ValueError(f"Fine {fine_id} not found for member {self.member_id}")

        fine.mark_as_paid()

    def pay_all_fines(self) -> Money:
        """Pay all unpaid fines"""
        total_paid = Money(0.0)

        for fine in self.fines:
            if not fine.is_paid:
                fine.mark_as_paid()
                total_paid = total_paid.add(fine.amount)

        return total_paid

    def get_total_unpaid_fines(self) -> Money:
        """Calculate total unpaid fine amount"""
        total = 0.0
        for fine in self.fines:
            if not fine.is_paid:
                total += fine.amount.amount

        return Money(total)

    def add_active_loan(self, loan_id: str) -> None:
        """Add a loan ID to active loans"""
        if loan_id not in self.active_loan_ids:
            self.active_loan_ids.append(loan_id)

    def remove_active_loan(self, loan_id: str) -> None:
        """Remove a loan ID from active loans"""
        if loan_id in self.active_loan_ids:
            self.active_loan_ids.remove(loan_id)

    def get_borrowing_capacity(self) -> int:
        """Get remaining borrowing capacity"""
        return 5 - len(self.active_loan_ids)

    def is_premium_member(self) -> bool:
        """Check if member has premium privileges"""
        return self.member_type == MemberType.PREMIUM

    def _find_fine_by_id(self, fine_id: str) -> Optional[Fine]:
        """Find fine by ID within this aggregate"""
        return next((fine for fine in self.fines if fine.fine_id == fine_id), None)

    def __str__(self):
        return f"Member({self.name}, {self.email.value}, {self.member_type.value})"

    def __eq__(self, other):
        if not isinstance(other, Member):
            return False
        return self.member_id == other.member_id