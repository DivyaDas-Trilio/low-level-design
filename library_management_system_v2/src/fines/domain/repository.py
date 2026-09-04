from abc import abstractmethod

from shared.base_repo import Repository
from shared.ids import FineId, MemberId
from fines.domain.fine import Fine


class FineRepository(Repository[FineId, Fine]):
    """Persistence port for the Fine aggregate. get/save are inherited."""

    @abstractmethod
    def find_unpaid_by_member(self, member_id: MemberId) -> list[Fine]:
        """UC-6: a member's outstanding (UNPAID) fines."""
        ...
