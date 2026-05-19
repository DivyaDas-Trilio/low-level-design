"""Repository interface for Book aggregate"""

from abc import ABC, abstractmethod
from typing import List, Optional

from ..entities import Book


class BookRepository(ABC):
    """Repository interface for Book aggregate root"""

    @abstractmethod
    def find_by_id(self, book_id: str) -> Optional[Book]:
        """Find book by unique identifier"""
        pass

    @abstractmethod
    def find_by_isbn(self, isbn: str) -> Optional[Book]:
        """Find book by ISBN"""
        pass

    @abstractmethod
    def save(self, book: Book) -> None:
        """Save or update book aggregate"""
        pass

    @abstractmethod
    def delete(self, book: Book) -> None:
        """Remove book from repository"""
        pass

    @abstractmethod
    def find_available_books(self, title: Optional[str] = None,
                           author: Optional[str] = None,
                           genre: Optional[str] = None,
                           limit: int = 50) -> List[Book]:
        """Search available books with optional filters"""
        pass

    @abstractmethod
    def find_all_books(self, title: Optional[str] = None,
                      author: Optional[str] = None,
                      genre: Optional[str] = None,
                      limit: int = 50) -> List[Book]:
        """Search all books (available and borrowed) with filters"""
        pass

    @abstractmethod
    def find_by_title(self, title: str) -> List[Book]:
        """Find books by exact title match"""
        pass

    @abstractmethod
    def find_by_author(self, author: str) -> List[Book]:
        """Find books by author"""
        pass

    @abstractmethod
    def find_by_genre(self, genre: str) -> List[Book]:
        """Find books by genre"""
        pass

    @abstractmethod
    def find_popular_books(self, limit: int = 10) -> List[Book]:
        """Find most borrowed books"""
        pass

    @abstractmethod
    def count_total_books(self) -> int:
        """Get total count of books in library"""
        pass

    @abstractmethod
    def count_available_books(self) -> int:
        """Get count of currently available books"""
        pass

    @abstractmethod
    def find_recently_added(self, days: int = 30, limit: int = 20) -> List[Book]:
        """Find books added in the last N days"""
        pass