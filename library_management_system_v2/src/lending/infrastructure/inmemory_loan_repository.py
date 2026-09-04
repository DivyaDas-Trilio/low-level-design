from datetime import date

from shared.exceptions import EntityNotFoundError
from shared.ids import LoanId, MemberId
from lending.domain.loan import Loan
from lending.domain.enums import LoanStatus
from lending.domain.repository import LoanRepository


class InMemoryLoanRepository(LoanRepository):
    def __init__(self):
        self._db: dict[LoanId, Loan] = {}

    def get(self, entity_id: LoanId) -> Loan:
        try:
            return self._db[entity_id]
        except KeyError:
            raise EntityNotFoundError(str(entity_id))

    def save(self, aggregate: Loan) -> None:
        self._db[aggregate.id] = aggregate                  # upsert, keyed by id

    def count_active_for_member(self, member_id: MemberId) -> int:
        # "active" = still OUT (not returned) — ACTIVE *and* OVERDUE both count
        # toward the <= 2 limit, since an overdue copy is still with the member.
        return sum(
            1 for ln in self._db.values()
            if ln.member_id == member_id and ln.status is not LoanStatus.RETURNED
        )

    def find_overdue(self, as_of: date) -> list[Loan]:
        return [ln for ln in self._db.values() if ln.is_overdue(as_of)]
