"""Catalog HTTP controller — a thin driving adapter.

Each endpoint: parse the request DTO -> call ONE CatalogService method -> map the
result to a response DTO. No business logic, no try/except (DomainError bubbles
to the one app-level handler in app.py).
"""

from fastapi import APIRouter, Depends

from shared.ids import BookId, CopyId
from catalog.domain.book import Book
from catalog.application.catalog_service import CatalogService
from catalog.api.dependencies import get_catalog_service
from catalog.api.dtos import (
    AddBookRequest, UpdateBookRequest,
    AddBookResponse, AddCopyResponse, BookResponse, AvailabilityResponse,
)

router = APIRouter(prefix="/catalog", tags=["catalog"])


def _to_book_response(b: Book) -> BookResponse:          # map entity -> DTO (never leak the entity)
    return BookResponse(book_id=str(b.id), title=b.title, author=b.author,
                        isbn=b.isbn.value, genre=b.genre)


# ---- UC-9: manage books & copies ----
@router.post("/books", response_model=AddBookResponse, status_code=201)
def add_book(req: AddBookRequest, svc: CatalogService = Depends(get_catalog_service)):
    book_id = svc.add_book(req.isbn, req.title, req.author, req.genre)
    return AddBookResponse(book_id=str(book_id))


@router.post("/books/{book_id}/copies", response_model=AddCopyResponse, status_code=201)
def add_copy(book_id: str, svc: CatalogService = Depends(get_catalog_service)):
    copy_id = svc.add_copy(BookId(book_id))
    return AddCopyResponse(copy_id=str(copy_id))


@router.patch("/books/{book_id}", status_code=204)
def update_book(book_id: str, req: UpdateBookRequest,
                svc: CatalogService = Depends(get_catalog_service)):
    svc.update_book(BookId(book_id), title=req.title, genre=req.genre)


@router.delete("/books/{book_id}", status_code=204)
def remove_book(book_id: str, svc: CatalogService = Depends(get_catalog_service)):
    svc.remove_book(BookId(book_id))


@router.delete("/copies/{copy_id}", status_code=204)
def remove_copy(copy_id: str, svc: CatalogService = Depends(get_catalog_service)):
    svc.remove_copy(CopyId(copy_id))


# ---- UC-8: mark a copy damaged / lost ----
@router.post("/copies/{copy_id}/damaged", status_code=204)
def mark_damaged(copy_id: str, svc: CatalogService = Depends(get_catalog_service)):
    svc.mark_copy_damaged(CopyId(copy_id))


@router.post("/copies/{copy_id}/lost", status_code=204)
def mark_lost(copy_id: str, svc: CatalogService = Depends(get_catalog_service)):
    svc.mark_copy_lost(CopyId(copy_id))


# ---- UC-7: search ----
@router.get("/books/search", response_model=list[BookResponse])
def search(keyword: str, svc: CatalogService = Depends(get_catalog_service)):
    return [_to_book_response(b) for b in svc.search_books(keyword)]


# ---- UC-3: availability (catalog side) ----
@router.get("/books/{book_id}/availability", response_model=AvailabilityResponse)
def availability(book_id: str, svc: CatalogService = Depends(get_catalog_service)):
    return AvailabilityResponse(book_id=book_id,
                                available_copies=svc.count_available(BookId(book_id)))
