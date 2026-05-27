"""Data Transfer Objects for Application Layer"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List


# Request DTOs
@dataclass
class RegisterMemberRequest:
    """Request to register a new member"""
    name: str
    email: str
    member_type: str = "REGULAR"
    phone: Optional[str] = None


@dataclass
class AddBookRequest:
    """Request to add a new book"""
    title: str
    author: str
    isbn: str
    genre: Optional[str] = None


@dataclass
class BorrowBookRequest:
    """Request to borrow a book"""
    member_id: str
    book_id: str


@dataclass
class ReturnBookRequest:
    """Request to return a book"""
    loan_id: str
    return_date: Optional[datetime] = None


@dataclass
class PayFineRequest:
    """Request to pay fines"""
    member_id: str
    fine_ids: Optional[List[str]] = None  # None means pay all fines


@dataclass
class BookSearchRequest:
    """Request to search books"""
    title: Optional[str] = None
    author: Optional[str] = None
    genre: Optional[str] = None
    available_only: bool = True
    limit: int = 50


# Response DTOs
@dataclass
class RegisterMemberResponse:
    """Response after member registration"""
    success: bool
    member_id: str
    library_card_number: str
    message: str


@dataclass
class AddBookResponse:
    """Response after adding a book"""
    success: bool
    book_id: str
    message: str


@dataclass
class BorrowBookResponse:
    """Response after borrowing a book"""
    success: bool
    loan_id: str
    due_date: datetime
    message: str


@dataclass
class ReturnBookResponse:
    """Response after returning a book"""
    success: bool
    return_date: datetime
    fine_amount: float
    message: str


@dataclass
class PayFineResponse:
    """Response after paying fines"""
    success: bool
    total_paid: float
    remaining_balance: float
    message: str


@dataclass
class BookSearchResponse:
    """Response for book search"""
    books: List[dict]  # Book details as dictionaries
    total_count: int
    has_more: bool


# View DTOs (for read operations)
@dataclass
class MemberDetailsView:
    """View of member details"""
    member_id: str
    name: str
    email: str
    member_type: str
    library_card_number: str
    active_loans_count: int
    total_unpaid_fines: float
    member_since: datetime


@dataclass
class BookDetailsView:
    """View of book details"""
    book_id: str
    title: str
    author: str
    isbn: str
    genre: Optional[str]
    is_available: bool
    total_borrows: int
    last_borrowed_date: Optional[datetime]


@dataclass
class LoanDetailsView:
    """View of loan details"""
    loan_id: str
    member_id: str
    member_name: str
    book_id: str
    book_title: str
    borrow_date: datetime
    due_date: datetime
    return_date: Optional[datetime]
    status: str
    overdue_days: int
    fine_amount: float


@dataclass
class LibraryStatsView:
    """View of library statistics"""
    total_books: int
    available_books: int
    total_members: int
    active_loans: int
    overdue_loans: int
    total_unpaid_fines: float