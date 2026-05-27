"""Loan-related API models"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from enum import Enum


class LoanStatusEnum(str, Enum):
    ACTIVE = "ACTIVE"
    RETURNED = "RETURNED"
    OVERDUE = "OVERDUE"


class BorrowBookRequest(BaseModel):
    """Request model for borrowing a book"""
    book_id: str = Field(..., description="ID of the book to borrow")


class ReturnBookRequest(BaseModel):
    """Request model for returning a book"""
    return_date: Optional[datetime] = Field(None, description="Return date (defaults to current time)")


class ExtendLoanRequest(BaseModel):
    """Request model for extending a loan"""
    additional_days: int = Field(..., ge=1, le=30, description="Number of additional days")


class LoanResponse(BaseModel):
    """Basic loan response model"""
    loan_id: str
    member_id: str
    book_id: str
    borrow_date: datetime
    due_date: datetime
    return_date: Optional[datetime] = None
    status: str

    class Config:
        from_attributes = True


class LoanDetailResponse(LoanResponse):
    """Detailed loan response with additional information"""
    member_name: str
    book_title: str
    book_author: str
    days_until_due: int
    overdue_days: int
    fine_amount: float
    can_extend: bool


class BorrowBookResponse(BaseModel):
    """Response after borrowing a book"""
    loan_id: str
    due_date: datetime
    message: str
    loan_period_days: int


class ReturnBookResponse(BaseModel):
    """Response after returning a book"""
    return_date: datetime
    was_overdue: bool
    fine_amount: float
    message: str


class LoanHistoryRequest(BaseModel):
    """Request model for loan history"""
    member_id: Optional[str] = Field(None, description="Filter by member ID")
    book_id: Optional[str] = Field(None, description="Filter by book ID")
    status: Optional[LoanStatusEnum] = Field(None, description="Filter by status")
    start_date: Optional[datetime] = Field(None, description="Start date for date range")
    end_date: Optional[datetime] = Field(None, description="End date for date range")
    page: int = Field(default=1, ge=1)
    limit: int = Field(default=20, ge=1, le=100)


class OverdueLoansResponse(BaseModel):
    """Response for overdue loans report"""
    loans: List[LoanDetailResponse]
    total_count: int
    total_fine_amount: float