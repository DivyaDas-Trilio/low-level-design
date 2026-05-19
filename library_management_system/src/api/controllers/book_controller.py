"""Book management API endpoints"""

from fastapi import APIRouter, HTTPException, Depends, status, Query
from typing import List, Optional
from datetime import datetime

# Import API models
from ..models.book_models import (
    CreateBookRequest, UpdateBookRequest, BookResponse,
    BookDetailResponse, BookSearchRequest, BookStatsResponse
)
from ..models.common import SuccessResponse, PaginatedResponse

router = APIRouter(prefix="/api/books", tags=["books"])


# Dependency injection placeholder
async def get_library_service():
    """Dependency to get the library application service"""
    return None


@router.post("/",
             response_model=BookResponse,
             status_code=status.HTTP_201_CREATED,
             summary="Add a new book to the library")
async def add_book(
    request: CreateBookRequest,
    service = Depends(get_library_service)
):
    """
    Add a new book to the library catalog.

    - **title**: Book title (required)
    - **author**: Book author (required)
    - **isbn**: ISBN-10 or ISBN-13 (required)
    - **genre**: Book genre (optional)

    Returns the created book information.
    """
    from ...application.dtos import AddBookRequest as AppRequest

    app_request = AppRequest(
        title=request.title,
        author=request.author,
        isbn=request.isbn,
        genre=request.genre
    )

    result = await service.add_book(app_request)

    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.message
        )

    return BookResponse(
        book_id=result.book_id,
        title=request.title,
        author=request.author,
        isbn=request.isbn,
        genre=request.genre,
        is_available=True,
        added_date=datetime.now()
    )


@router.get("/{book_id}",
            response_model=BookDetailResponse,
            summary="Get book details")
async def get_book_details(
    book_id: str,
    service = Depends(get_library_service)
):
    """
    Get detailed information about a specific book.

    Returns book information including:
    - Basic details (title, author, ISBN, genre)
    - Availability status
    - Borrowing statistics
    - Current borrower information (if borrowed)
    """
    # This would call the book service to get details
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Get book details not implemented yet"
    )


@router.put("/{book_id}",
            response_model=BookResponse,
            summary="Update book information")
async def update_book(
    book_id: str,
    request: UpdateBookRequest,
    service = Depends(get_library_service)
):
    """
    Update book information.

    - **title**: Updated title (optional)
    - **author**: Updated author (optional)
    - **genre**: Updated genre (optional)

    Note: ISBN cannot be updated as it's the book's unique identifier.
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Book update not implemented yet"
    )


@router.delete("/{book_id}",
               status_code=status.HTTP_204_NO_CONTENT,
               summary="Remove a book from the library")
async def delete_book(
    book_id: str,
    service = Depends(get_library_service)
):
    """
    Remove a book from the library catalog.

    Note: Books that are currently borrowed cannot be deleted.
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Book deletion not implemented yet"
    )


@router.get("/",
            response_model=PaginatedResponse,
            summary="Search books")
async def search_books(
    title: Optional[str] = Query(None, description="Filter by title (partial match)"),
    author: Optional[str] = Query(None, description="Filter by author (partial match)"),
    genre: Optional[str] = Query(None, description="Filter by genre"),
    isbn: Optional[str] = Query(None, description="Filter by ISBN"),
    available_only: bool = Query(True, description="Show only available books"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    service = Depends(get_library_service)
):
    """
    Search books with various filters.

    Returns paginated list of books matching the criteria.
    """
    from ...application.dtos import BookSearchRequest as AppRequest

    app_request = AppRequest(
        title=title,
        author=author,
        genre=genre,
        available_only=available_only,
        limit=limit
    )

    result = await service.search_books(app_request)

    return PaginatedResponse(
        items=result.books,
        total_count=result.total_count,
        page=page,
        limit=limit,
        has_more=result.has_more
    )


@router.get("/isbn/{isbn}",
            response_model=BookResponse,
            summary="Get book by ISBN")
async def get_book_by_isbn(
    isbn: str,
    service = Depends(get_library_service)
):
    """
    Get book information by ISBN.

    - **isbn**: The ISBN-10 or ISBN-13 of the book
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Get book by ISBN not implemented yet"
    )


@router.get("/author/{author}",
            response_model=List[BookResponse],
            summary="Get books by author")
async def get_books_by_author(
    author: str,
    available_only: bool = Query(False, description="Show only available books"),
    service = Depends(get_library_service)
):
    """
    Get all books by a specific author.

    - **author**: Author name (exact match)
    - **available_only**: Whether to show only available books
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Get books by author not implemented yet"
    )


@router.get("/genre/{genre}",
            response_model=List[BookResponse],
            summary="Get books by genre")
async def get_books_by_genre(
    genre: str,
    available_only: bool = Query(False, description="Show only available books"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of results"),
    service = Depends(get_library_service)
):
    """
    Get books by genre.

    - **genre**: Genre name (exact match)
    - **available_only**: Whether to show only available books
    - **limit**: Maximum number of books to return
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Get books by genre not implemented yet"
    )


@router.get("/popular",
            response_model=List[BookResponse],
            summary="Get popular books")
async def get_popular_books(
    limit: int = Query(10, ge=1, le=50, description="Number of books to return"),
    service = Depends(get_library_service)
):
    """
    Get the most popular (most borrowed) books.

    - **limit**: Number of popular books to return (max 50)
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Get popular books not implemented yet"
    )


@router.get("/recent",
            response_model=List[BookResponse],
            summary="Get recently added books")
async def get_recently_added_books(
    days: int = Query(30, ge=1, le=365, description="Number of days to look back"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of results"),
    service = Depends(get_library_service)
):
    """
    Get recently added books.

    - **days**: Number of days to look back (default: 30)
    - **limit**: Maximum number of books to return
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Get recent books not implemented yet"
    )


@router.get("/stats",
            response_model=BookStatsResponse,
            summary="Get book statistics")
async def get_book_statistics(
    service = Depends(get_library_service)
):
    """
    Get library book statistics.

    Returns:
    - Total number of books
    - Number of available books
    - Number of borrowed books
    - List of popular books
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Book statistics not implemented yet"
    )