from shared.exceptions import EntityNotFoundError
from shared.ids import BookId
from catalog.domain.book import Book
from catalog.domain.repository.book_repo import BookRepository


class InMemoryBookRepository(BookRepository):
    def __init__(self):
        self._db: dict[BookId, Book] = {}

    def get(self, book_id: BookId) -> Book:
        try:
            return self._db[book_id]
        except KeyError:
            raise EntityNotFoundError(str(book_id))

    def save(self, book: Book) -> None:
        self._db[book.id] = book                       # upsert, keyed by id

    def search(self, keyword: str) -> list[Book]:
        return [b for b in self._db.values() if b.matches(keyword)]

    def delete(self, book_id: BookId) -> None:
        self._db.pop(book_id, None)                    # idempotent
