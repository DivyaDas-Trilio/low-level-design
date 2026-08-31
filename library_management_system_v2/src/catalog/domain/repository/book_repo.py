from abc import abstractmethod

from shared.base_repo import Repository
from shared.ids import BookId
from catalog.domain.book import Book


class BookRepository(Repository[BookId, Book]):
    """get(book_id) / save(book) are inherited from Repository — only add Book-specific queries."""

    @abstractmethod
    def search(self, keyword: str) -> list[Book]:
        """UC-7: books whose title/author matches the keyword."""
        ...

    @abstractmethod
    def delete(self, book_id: BookId) -> None:
        """UC-9: remove a book from the catalog (idempotent)."""
        ...
