"""Catalog subdomain — Books & their physical Copies.

Depends only on the `shared` kernel. Never imports another subdomain's internals.
"""

from catalog.domain.exceptions import (
    InvalidISBNError, CopyNotAvailableError, IllegalStatusTransitionError,
)
from catalog.domain.enums import CopyStatus
from catalog.domain.isbn import ISBN
from catalog.domain.book import Book
from catalog.domain.bookcopy import BookCopy

__all__ = [
    "InvalidISBNError", "CopyNotAvailableError", "IllegalStatusTransitionError",
    "CopyStatus", "ISBN", "Book", "BookCopy",
]
