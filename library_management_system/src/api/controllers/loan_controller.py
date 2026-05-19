"""Loan management API endpoints"""

from fastapi import APIRouter, HTTPException, Depends, status, Query, Path
from typing import List, Optional
from datetime import datetime

# Import API models
from ..models.loan_models import (
    BorrowBookRequest, ReturnBookRequest, ExtendLoanRequest,
    LoanResponse, LoanDetailResponse, BorrowBookResponse, ReturnBookResponse,
    LoanHistoryRequest, OverdueLoansResponse, LoanStatusEnum
)
from ..models.common import SuccessResponse, PaginatedResponse

router = APIRouter(prefix="/api/loans", tags=["loans"])


# Dependency injection placeholder
async def get_library_service():
    """Dependency to get the library application service"""
    return None


@router.post("/borrow/{member_id}",
             response_model=BorrowBookResponse,
             status_code=status.HTTP_201_CREATED,
             summary="Borrow a book")
async def borrow_book(
    member_id: str = Path(..., description="ID of the member borrowing the book"),
    request: BorrowBookRequest = ...,
    service = Depends(get_library_service)
):
    """
    Allow a member to borrow a book.

    - **member_id**: ID of the member (path parameter)
    - **book_id**: ID of the book to borrow (request body)

    Returns loan information including due date and loan terms.

    Business rules enforced:
    - Member must not have unpaid fines
    - Member must not exceed borrowing limit (5 books for regular, 10 for premium)
    - Book must be available
    - Member's library card must be valid
    """
    from ...application.dtos import BorrowBookRequest as AppRequest

    app_request = AppRequest(
        member_id=member_id,
        book_id=request.book_id
    )

    result = await service.borrow_book(app_request)

    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.message
        )

    return BorrowBookResponse(
        loan_id=result.loan_id,
        due_date=result.due_date,
        message=result.message,
        loan_period_days=14  # This should come from domain service based on member type
    )


@router.put("/{loan_id}/return",
            response_model=ReturnBookResponse,
            summary="Return a borrowed book")
async def return_book(
    loan_id: str = Path(..., description="ID of the loan to return"),
    request: ReturnBookRequest = ReturnBookRequest(),
    service = Depends(get_library_service)
):
    """
    Return a borrowed book.

    - **loan_id**: ID of the loan to return
    - **return_date**: Optional return date (defaults to current time)

    Returns information about the return including any fines incurred.

    Business rules enforced:
    - Loan must exist and be active
    - Fine is calculated for overdue returns
    - Book becomes available for other members
    """
    from ...application.dtos import ReturnBookRequest as AppRequest

    app_request = AppRequest(
        loan_id=loan_id,
        return_date=request.return_date
    )

    result = await service.return_book(app_request)

    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.message
        )

    return ReturnBookResponse(
        return_date=result.return_date,
        was_overdue=result.fine_amount > 0,
        fine_amount=result.fine_amount,
        message=result.message
    )


@router.get("/{loan_id}",
            response_model=LoanDetailResponse,
            summary="Get loan details")
async def get_loan_details(
    loan_id: str = Path(..., description="ID of the loan"),
    service = Depends(get_library_service)
):
    """
    Get detailed information about a specific loan.

    Returns complete loan information including:
    - Loan details (dates, status)
    - Member information
    - Book information
    - Fine calculations
    - Extension eligibility
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Get loan details not implemented yet"
    )


@router.put("/{loan_id}/extend",
            response_model=SuccessResponse,
            summary="Extend loan period")
async def extend_loan(
    loan_id: str = Path(..., description="ID of the loan to extend"),
    request: ExtendLoanRequest = ...,
    service = Depends(get_library_service)
):
    """
    Extend the loan period for a borrowed book.

    - **loan_id**: ID of the loan to extend
    - **additional_days**: Number of additional days (1-30)

    Business rules enforced:
    - Loan must be active (not overdue or already returned)
    - Member must not have unpaid fines
    - Extension limits based on member type (premium members get more extensions)
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Loan extension not implemented yet"
    )


@router.get("/",
            response_model=PaginatedResponse,
            summary="Get loan history")
async def get_loan_history(
    member_id: Optional[str] = Query(None, description="Filter by member ID"),
    book_id: Optional[str] = Query(None, description="Filter by book ID"),
    status: Optional[LoanStatusEnum] = Query(None, description="Filter by status"),
    start_date: Optional[datetime] = Query(None, description="Start date filter"),
    end_date: Optional[datetime] = Query(None, description="End date filter"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    service = Depends(get_library_service)
):
    """
    Get loan history with optional filters.

    Supports filtering by:
    - Member ID
    - Book ID
    - Loan status
    - Date range

    Returns paginated results.
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Loan history not implemented yet"
    )


@router.get("/overdue",
            response_model=OverdueLoansResponse,
            summary="Get overdue loans")
async def get_overdue_loans(
    limit: int = Query(50, ge=1, le=200, description="Maximum number of results"),
    service = Depends(get_library_service)
):
    """
    Get all currently overdue loans.

    Returns:
    - List of overdue loans with member and book details
    - Total count of overdue loans
    - Total fine amount across all overdue loans

    Useful for library staff to follow up on overdue books.
    """
    overdue_loans = await service.get_overdue_loans()

    total_fines = sum(loan.fine_amount for loan in overdue_loans)

    return OverdueLoansResponse(
        loans=overdue_loans[:limit],
        total_count=len(overdue_loans),
        total_fine_amount=total_fines
    )


@router.get("/due-soon",
            response_model=List[LoanDetailResponse],
            summary="Get loans due soon")
async def get_loans_due_soon(
    days: int = Query(3, ge=1, le=14, description="Number of days ahead to check"),
    service = Depends(get_library_service)
):
    """
    Get loans that are due within the specified number of days.

    - **days**: Number of days to look ahead (default: 3)

    Useful for sending reminder notifications to members.
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Loans due soon not implemented yet"
    )


@router.get("/member/{member_id}",
            response_model=List[LoanDetailResponse],
            summary="Get member's loans")
async def get_member_loans(
    member_id: str = Path(..., description="ID of the member"),
    active_only: bool = Query(False, description="Show only active loans"),
    service = Depends(get_library_service)
):
    """
    Get all loans for a specific member.

    - **member_id**: ID of the member
    - **active_only**: Whether to show only active loans

    Returns complete loan history or just active loans for the member.
    """
    loan_history = await service.get_member_loan_history(member_id)

    if active_only:
        loan_history = [loan for loan in loan_history if loan.status == "ACTIVE"]

    return loan_history


@router.get("/book/{book_id}",
            response_model=List[LoanDetailResponse],
            summary="Get book's loan history")
async def get_book_loans(
    book_id: str = Path(..., description="ID of the book"),
    active_only: bool = Query(False, description="Show only active loans"),
    service = Depends(get_library_service)
):
    """
    Get loan history for a specific book.

    - **book_id**: ID of the book
    - **active_only**: Whether to show only active loans

    Useful for tracking book usage patterns and current borrower.
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Book loan history not implemented yet"
    )


@router.get("/stats",
            summary="Get loan statistics")
async def get_loan_statistics(
    service = Depends(get_library_service)
):
    """
    Get loan statistics for the library.

    Returns:
    - Total number of loans
    - Active loans count
    - Overdue loans count
    - Average loan duration
    - Popular borrowing times
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Loan statistics not implemented yet"
    )