from shared.exceptions import EntityNotFoundError
from shared.ids import BookId, CopyId
from catalog.domain.bookcopy import BookCopy
from catalog.domain.repository.book_copy_repo import BookCopyRepository


class InMemoryBookCopyRepository(BookCopyRepository):
    def __init__(self):
        self._db: dict[CopyId, BookCopy] = {}

    def get(self, entity_id: CopyId) -> BookCopy:
        try:
            return self._db[entity_id]
        except KeyError:
            raise EntityNotFoundError(str(entity_id))

    def save(self, aggregate: BookCopy) -> None:
        self._db[aggregate.copy_id] = aggregate                  # upsert, keyed by id

    def find_available_for_book(self, book_id: BookId) -> list[BookCopy]:
        return [c for c in self._db.values()
                if c.book_id == book_id and c.is_available]

    def delete(self, copy_id: CopyId) -> None:
        self._db.pop(copy_id, None)                    # idempotent
