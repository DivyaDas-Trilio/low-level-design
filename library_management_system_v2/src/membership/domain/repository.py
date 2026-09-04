from abc import abstractmethod

from shared.base_repo import Repository
from shared.ids import MemberId
from membership.domain.member import Member


class IMembershipRepository(Repository[MemberId, Member]):
    """Persistence port for the Member aggregate. get/save are inherited."""

    @abstractmethod
    def delete(self, member_id: MemberId) -> None:
        """UC-10: remove a member (idempotent)."""
        ...

    @abstractmethod
    def exists_email(self, email: str) -> bool:
        """Register-time uniqueness check against the member's email."""
        ...
