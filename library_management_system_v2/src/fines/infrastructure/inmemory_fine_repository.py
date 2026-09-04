from shared.exceptions import EntityNotFoundError
from shared.ids import FineId, MemberId
from fines.domain.fine import Fine
from fines.domain.enums import FineStatus
from fines.domain.repository import FineRepository


class InMemoryFineRepository(FineRepository):
    def __init__(self):
        self._db: dict[FineId, Fine] = {}

    def get(self, entity_id: FineId) -> Fine:
        try:
            return self._db[entity_id]
        except KeyError:
            raise EntityNotFoundError(str(entity_id))

    def save(self, aggregate: Fine) -> None:
        self._db[aggregate.id] = aggregate                  # upsert, keyed by id

    def find_unpaid_by_member(self, member_id: MemberId) -> list[Fine]:
        return [
            f for f in self._db.values()
            if f.member_id == member_id and f.status is FineStatus.UNPAID
        ]
