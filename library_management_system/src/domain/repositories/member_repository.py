"""Repository interface for Member aggregate"""

from abc import ABC, abstractmethod
from typing import List, Optional

from ..entities import Member


class MemberRepository(ABC):
    """Repository interface for Member aggregate root"""

    @abstractmethod
    def find_by_id(self, member_id: str) -> Optional[Member]:
        """Find member by unique identifier"""
        pass

    @abstractmethod
    def find_by_email(self, email: str) -> Optional[Member]:
        """Find member by email address"""
        pass

    @abstractmethod
    def find_by_card_number(self, card_number: str) -> Optional[Member]:
        """Find member by library card number"""
        pass

    @abstractmethod
    def save(self, member: Member) -> None:
        """Save or update member aggregate"""
        pass

    @abstractmethod
    def delete(self, member: Member) -> None:
        """Remove member from repository"""
        pass

    @abstractmethod
    def find_members_with_overdue_books(self) -> List[Member]:
        """Find all members who have overdue books (for notifications)"""
        pass

    @abstractmethod
    def find_members_with_unpaid_fines(self) -> List[Member]:
        """Find all members with unpaid fines"""
        pass

    @abstractmethod
    def find_premium_members(self) -> List[Member]:
        """Find all premium members (for special promotions)"""
        pass

    @abstractmethod
    def count_total_members(self) -> int:
        """Get total count of registered members"""
        pass

    @abstractmethod
    def find_members_by_name_pattern(self, name_pattern: str) -> List[Member]:
        """Search members by name pattern"""
        pass