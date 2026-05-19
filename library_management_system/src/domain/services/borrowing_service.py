"""Domain service for book borrowing business logic"""

from datetime import datetime, timedelta
from typing import Optional

from ..entities import Member, Book
from ..value_objects import MemberType


class BookBorrowingDomainService:
    """Domain service handling borrowing business rules across aggregates"""

    def can_member_borrow_book(self, member: Member, book: Book) -> bool:
        """
        Business rule: Determine if a specific member can borrow a specific book
        This spans Member and Book aggregates, so it belongs in a domain service
        """
        # Check member eligibility
        if not member.can_borrow_book():
            return False

        # Check book availability
        if not book.is_available:
            return False

        return True

    def calculate_loan_period(self, member_type: MemberType) -> int:
        """
        Business rule: Different member types get different loan periods
        """
        if member_type == MemberType.PREMIUM:
            return 21  # 3 weeks for premium members
        elif member_type == MemberType.STUDENT:
            return 30  # 1 month for students
        else:
            return 14  # 2 weeks for regular members

    def calculate_due_date(self, member: Member, borrow_date: Optional[datetime] = None) -> datetime:
        """
        Calculate due date based on member type and borrow date
        """
        if borrow_date is None:
            borrow_date = datetime.now()

        loan_period = self.calculate_loan_period(member.member_type)
        return borrow_date + timedelta(days=loan_period)

    def can_extend_loan(self, member: Member, current_extensions: int = 0) -> bool:
        """
        Business rule: Loan extension eligibility
        - Premium members: unlimited extensions
        - Regular/Student: max 2 extensions
        - No extensions if member has unpaid fines
        """
        if member.get_total_unpaid_fines().amount > 0:
            return False

        if member.member_type == MemberType.PREMIUM:
            return True

        return current_extensions < 2

    def calculate_max_borrowing_limit(self, member: Member) -> int:
        """
        Business rule: Different member types have different borrowing limits
        """
        if member.member_type == MemberType.PREMIUM:
            return 10  # Premium members can borrow more
        else:
            return 5   # Regular and student members

    def get_borrowing_priority(self, member: Member) -> int:
        """
        Business rule: Borrowing priority for reserved books
        Higher number = higher priority
        """
        if member.member_type == MemberType.PREMIUM:
            return 3
        elif member.member_type == MemberType.STUDENT:
            return 2
        else:
            return 1

    def validate_borrowing_request(self, member: Member, book: Book) -> list[str]:
        """
        Validate a borrowing request and return list of validation errors
        Returns empty list if valid
        """
        errors = []

        # Check library card validity
        if not member.library_card.is_valid():
            errors.append("Library card has expired")

        # Check borrowing limit
        max_limit = self.calculate_max_borrowing_limit(member)
        if len(member.active_loan_ids) >= max_limit:
            errors.append(f"Borrowing limit reached ({max_limit} books)")

        # Check unpaid fines
        if member.get_total_unpaid_fines().amount > 0:
            errors.append("Cannot borrow with unpaid fines")

        # Check book availability
        if not book.is_available:
            errors.append("Book is not available")

        return errors