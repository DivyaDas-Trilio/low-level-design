from abc import abstractmethod
from datetime import date

from shared.base_repo import Repository
from shared.ids import LoanId, MemberId
from lending.domain.loan import Loan


class LoanRepository(Repository[LoanId, Loan]):
    """Persistence port for the Loan aggregate. get/save are inherited.

    Only the queries real use cases need (ISP) — the 'navigate backwards' queries
    that by-ID references can't answer in memory (a Member holds no loan list).
    """

    @abstractmethod
    def count_active_for_member(self, member_id: MemberId) -> int:
        """UC-1: how many ACTIVE loans this member has (for the <= 2 rule)."""
        ...

    @abstractmethod
    def find_overdue(self, as_of: date) -> list[Loan]:
        """UC-5: loans whose due date has passed and aren't returned."""
        ...
