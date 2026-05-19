"""Repository interface for Loan aggregate"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional

from ..entities import Loan
from ..value_objects import LoanStatus


class LoanRepository(ABC):
    """Repository interface for Loan aggregate root"""

    @abstractmethod
    def find_by_id(self, loan_id: str) -> Optional[Loan]:
        """Find loan by unique identifier"""
        pass

    @abstractmethod
    def save(self, loan: Loan) -> None:
        """Save or update loan aggregate"""
        pass

    @abstractmethod
    def delete(self, loan: Loan) -> None:
        """Remove loan from repository"""
        pass

    @abstractmethod
    def find_active_loans_for_member(self, member_id: str) -> List[Loan]:
        """Find all active loans for a specific member"""
        pass

    @abstractmethod
    def find_all_loans_for_member(self, member_id: str) -> List[Loan]:
        """Find all loans (active and returned) for a specific member"""
        pass

    @abstractmethod
    def find_loans_for_book(self, book_id: str) -> List[Loan]:
        """Find all loans for a specific book"""
        pass

    @abstractmethod
    def find_overdue_loans(self) -> List[Loan]:
        """Find all currently overdue loans"""
        pass

    @abstractmethod
    def find_loans_due_soon(self, days: int = 3) -> List[Loan]:
        """Find loans due within specified number of days"""
        pass

    @abstractmethod
    def count_active_loans_for_member(self, member_id: str) -> int:
        """Quick count of active loans for borrowing limit checks"""
        pass

    @abstractmethod
    def find_loans_by_status(self, status: LoanStatus) -> List[Loan]:
        """Find loans by status"""
        pass

    @abstractmethod
    def find_loans_by_date_range(self, start_date: datetime,
                                end_date: datetime) -> List[Loan]:
        """Find loans borrowed within date range"""
        pass

    @abstractmethod
    def find_longest_overdue_loans(self, limit: int = 10) -> List[Loan]:
        """Find most overdue loans for priority follow-up"""
        pass

    @abstractmethod
    def count_total_loans(self) -> int:
        """Get total count of all loans"""
        pass

    @abstractmethod
    def count_active_loans(self) -> int:
        """Get count of currently active loans"""
        pass

    @abstractmethod
    def get_borrowing_statistics(self, member_id: str) -> dict:
        """Get borrowing statistics for a member"""
        pass