from shared.exceptions import EntityNotFoundError
from shared.ids import BookId
from catalog.domain.book import Book
from catalog.domain.repository.book_repo import BookRepository


class InMemoryBookRepository(BookRepository):
    def __init__(self):
        self._db: dict[BookId, Book] = {}

    def get(self, entity_id: BookId) -> Book:
        try:
            return self._db[entity_id]
        except KeyError:
            raise EntityNotFoundError(str(entity_id))

    def save(self, aggregate: Book) -> None:
        self._db[aggregate.id] = aggregate                       # upsert, keyed by id

    def search(self, keyword: str) -> list[Book]:
        return [b for b in self._db.values() if b.matches(keyword)]

    def delete(self, book_id: BookId) -> None:
        self._db.pop(book_id, None)                    # idempotent
