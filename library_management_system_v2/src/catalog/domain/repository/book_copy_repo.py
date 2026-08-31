from abc import abstractmethod

from shared.base_repo import Repository
from shared.ids import BookId, CopyId
from catalog.domain.bookcopy import BookCopy


class BookCopyRepository(Repository[CopyId, BookCopy]):
    """get(copy_id) / save(copy) are inherited — only add BookCopy-specific queries."""

    @abstractmethod
    def find_available_for_book(self, book_id: BookId) -> list[BookCopy]:
        """UC-3: available copies for a given book."""
        ...

    @abstractmethod
    def delete(self, copy_id: CopyId) -> None:
        """UC-9: remove a copy (idempotent)."""
        ...
