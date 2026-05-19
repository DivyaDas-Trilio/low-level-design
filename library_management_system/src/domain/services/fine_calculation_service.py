"""Domain service for fine and penalty calculations"""

from datetime import datetime, timedelta
from typing import List

from ..entities import Loan, Member
from ..value_objects import Money, MemberType


class FineCalculationDomainService:
    """Domain service handling fine calculation business logic"""

    # Fine rates (could be configurable in real system)
    BASIC_DAILY_RATE = 1.0
    PREMIUM_DAILY_RATE = 0.5  # Premium members get reduced fines
    STUDENT_DAILY_RATE = 0.5  # Students get reduced fines
    ESCALATION_THRESHOLD_DAYS = 7
    ESCALATED_DAILY_RATE = 2.0

    def calculate_overdue_fine(self, loan: Loan, member: Member) -> Money:
        """
        Calculate fine for an overdue loan based on member type and overdue duration
        This is domain logic that spans Loan and Member aggregates
        """
        if not loan.is_overdue():
            return Money(0.0)

        overdue_days = loan.get_overdue_days()
        base_rate = self._get_daily_fine_rate(member.member_type)

        # Progressive fine calculation
        if overdue_days <= self.ESCALATION_THRESHOLD_DAYS:
            # Standard rate for first week
            total_fine = overdue_days * base_rate
        else:
            # Standard rate for first week, escalated rate after
            standard_days_fine = self.ESCALATION_THRESHOLD_DAYS * base_rate
            escalated_days = overdue_days - self.ESCALATION_THRESHOLD_DAYS
            escalated_fine = escalated_days * self.ESCALATED_DAILY_RATE
            total_fine = standard_days_fine + escalated_fine

        return Money(total_fine)

    def calculate_total_member_fines(self, member: Member, active_loans: List[Loan]) -> Money:
        """
        Calculate total outstanding fines for a member including active overdue loans
        """
        total = Money(0.0)

        # Existing unpaid fines
        total = total.add(member.get_total_unpaid_fines())

        # Potential fines from current overdue loans
        for loan in active_loans:
            if loan.is_overdue():
                potential_fine = self.calculate_overdue_fine(loan, member)
                total = total.add(potential_fine)

        return total

    def estimate_fine_if_returned_on_date(self, loan: Loan, member: Member,
                                        return_date: datetime) -> Money:
        """
        Estimate what fine would be if book is returned on a specific date
        Useful for showing members potential costs
        """
        if return_date <= loan.due_date:
            return Money(0.0)

        overdue_days = (return_date - loan.due_date).days
        base_rate = self._get_daily_fine_rate(member.member_type)

        if overdue_days <= self.ESCALATION_THRESHOLD_DAYS:
            fine_amount = overdue_days * base_rate
        else:
            standard_fine = self.ESCALATION_THRESHOLD_DAYS * base_rate
            escalated_days = overdue_days - self.ESCALATION_THRESHOLD_DAYS
            escalated_fine = escalated_days * self.ESCALATED_DAILY_RATE
            fine_amount = standard_fine + escalated_fine

        return Money(fine_amount)

    def get_fine_forgiveness_eligibility(self, member: Member) -> bool:
        """
        Business rule: Determine if member is eligible for fine forgiveness
        """
        # First-time offenders with small amounts might get forgiveness
        unpaid_amount = member.get_total_unpaid_fines().amount

        if unpaid_amount <= 5.0 and len(member.fines) <= 2:
            return True

        # Premium members get some forgiveness
        if member.member_type == MemberType.PREMIUM and unpaid_amount <= 10.0:
            return True

        return False

    def calculate_payment_plan(self, total_fine: Money, member: Member) -> List[Money]:
        """
        Business rule: Calculate payment plan based on fine amount and member type
        """
        if total_fine.amount <= 10.0:
            # Small amounts must be paid in full
            return [total_fine]

        # Larger amounts can be split
        if member.member_type == MemberType.STUDENT:
            # Students get more flexible payment plans
            num_installments = min(4, int(total_fine.amount / 5))
        else:
            num_installments = min(3, int(total_fine.amount / 10))

        installment_amount = total_fine.amount / num_installments
        return [Money(installment_amount) for _ in range(num_installments)]

    def _get_daily_fine_rate(self, member_type: MemberType) -> float:
        """Get daily fine rate based on member type"""
        if member_type == MemberType.PREMIUM:
            return self.PREMIUM_DAILY_RATE
        elif member_type == MemberType.STUDENT:
            return self.STUDENT_DAILY_RATE
        else:
            return self.BASIC_DAILY_RATE

    def get_fine_warning_threshold(self, member: Member) -> Money:
        """
        Business rule: At what fine amount should we warn/restrict the member
        """
        if member.member_type == MemberType.PREMIUM:
            return Money(50.0)  # Premium members get higher threshold
        elif member.member_type == MemberType.STUDENT:
            return Money(20.0)  # Students get lower threshold
        else:
            return Money(25.0)  # Regular members