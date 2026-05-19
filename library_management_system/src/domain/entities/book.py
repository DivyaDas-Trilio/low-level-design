"""Book entity - represents a book in the library catalog"""

from datetime import datetime
from typing import Optional
import uuid

from ..exceptions import InvalidISBNError, InvalidTitleError, BookNotAvailableError
from ..value_objects import ISBN


class Book:
    """Entity representing a book in the library"""

    def __init__(self, title: str, author: str, isbn: str, genre: Optional[str] = None,
                 book_id: Optional[str] = None):
        # Entity identity
        self.book_id = book_id or str(uuid.uuid4())

        # Invariant: Title cannot be empty
        if not title.strip():
            raise InvalidTitleError("Book title cannot be empty")

        # Invariant: Author cannot be empty
        if not author.strip():
            raise ValueError("Book author cannot be empty")

        # Invariant: ISBN must be valid (using value object)
        self.isbn = ISBN(isbn)

        # Entity state
        self.title = title.strip()
        self.author = author.strip()
        self.genre = genre.strip() if genre else None
        self.is_available = True
        self.added_date = datetime.now()

        # Track borrowing history (for statistics)
        self.total_borrows = 0
        self.last_borrowed_date: Optional[datetime] = None

    def mark_as_borrowed(self) -> None:
        """Mark book as borrowed"""
        # Invariant: Cannot borrow already borrowed book
        if not self.is_available:
            raise BookNotAvailableError(f"Book '{self.title}' is not available for borrowing")

        self.is_available = False
        self.total_borrows += 1
        self.last_borrowed_date = datetime.now()

    def mark_as_available(self) -> None:
        """Mark book as returned and available"""
        self.is_available = True

    def is_popular(self) -> bool:
        """Check if book is popular (borrowed more than 10 times)"""
        return self.total_borrows > 10

    def get_availability_status(self) -> str:
        """Get human-readable availability status"""
        return "Available" if self.is_available else "Borrowed"

    def matches_search(self, title: Optional[str] = None, author: Optional[str] = None,
                      genre: Optional[str] = None) -> bool:
        """Check if book matches search criteria"""
        if title and title.lower() not in self.title.lower():
            return False

        if author and author.lower() not in self.author.lower():
            return False

        if genre and self.genre and genre.lower() not in self.genre.lower():
            return False

        return True

    def __str__(self):
        status = "Available" if self.is_available else "Borrowed"
        return f"Book('{self.title}' by {self.author}) [{status}]"

    def __eq__(self, other):
        if not isinstance(other, Book):
            return False
        return self.book_id == other.book_id