"""API DTOs for the Catalog subdomain — the public HTTP contract.

Never expose domain entities on the wire; these Pydantic models decouple the
contract from the model, hide internals, and reshape data for clients.
"""

from pydantic import BaseModel


# ---- requests ----
class AddBookRequest(BaseModel):
    isbn: str
    title: str
    author: str
    genre: str | None = None


class UpdateBookRequest(BaseModel):
    title: str | None = None
    genre: str | None = None


# ---- responses ----
class AddBookResponse(BaseModel):
    book_id: str


class AddCopyResponse(BaseModel):
    copy_id: str


class BookResponse(BaseModel):
    book_id: str
    title: str
    author: str
    isbn: str
    genre: str | None = None


class AvailabilityResponse(BaseModel):
    book_id: str
    available_copies: int
