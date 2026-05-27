"""Book-related API models"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List


class CreateBookRequest(BaseModel):
    """Request model for adding a new book"""
    title: str = Field(..., min_length=1, max_length=200, description="Book title")
    author: str = Field(..., min_length=1, max_length=100, description="Book author")
    isbn: str = Field(..., min_length=10, max_length=17, description="ISBN-10 or ISBN-13")
    genre: Optional[str] = Field(None, max_length=50, description="Book genre")


class UpdateBookRequest(BaseModel):
    """Request model for updating book information"""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    author: Optional[str] = Field(None, min_length=1, max_length=100)
    genre: Optional[str] = Field(None, max_length=50)


class BookResponse(BaseModel):
    """Basic book response model"""
    book_id: str
    title: str
    author: str
    isbn: str
    genre: Optional[str] = None
    is_available: bool
    added_date: datetime

    class Config:
        from_attributes = True


class BookDetailResponse(BookResponse):
    """Detailed book response with borrowing statistics"""
    total_borrows: int
    last_borrowed_date: Optional[datetime] = None
    current_borrower_id: Optional[str] = None
    due_date: Optional[datetime] = None


class BookSearchRequest(BaseModel):
    """Request model for searching books"""
    title: Optional[str] = Field(None, description="Search by title (partial match)")
    author: Optional[str] = Field(None, description="Search by author (partial match)")
    genre: Optional[str] = Field(None, description="Search by genre (partial match)")
    isbn: Optional[str] = Field(None, description="Search by exact ISBN")
    available_only: bool = Field(default=True, description="Show only available books")
    page: int = Field(default=1, ge=1, description="Page number")
    limit: int = Field(default=20, ge=1, le=100, description="Items per page")


class BookStatsResponse(BaseModel):
    """Book statistics response"""
    total_books: int
    available_books: int
    borrowed_books: int
    popular_books: List[BookResponse]