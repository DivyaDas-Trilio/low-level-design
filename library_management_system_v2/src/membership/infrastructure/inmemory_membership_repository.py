from shared.exceptions import EntityNotFoundError
from shared.ids import MemberId
from membership.domain.member import Member
from membership.domain.repository import IMembershipRepository


class InMemoryMembershipRepository(IMembershipRepository):
    def __init__(self):
        self._db: dict[MemberId, Member] = {}

    def get(self, entity_id: MemberId) -> Member:
        try:
            return self._db[entity_id]
        except KeyError:
            raise EntityNotFoundError(str(entity_id))

    def save(self, aggregate: Member) -> None:
        self._db[aggregate.id] = aggregate                  # upsert, keyed by id (no raise)

    def delete(self, member_id: MemberId) -> None:
        self._db.pop(member_id, None)                       # idempotent

    def exists_email(self, email: str) -> bool:
        return any(m.email.value == email for m in self._db.values())
