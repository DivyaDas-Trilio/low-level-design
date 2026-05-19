"""Member management API endpoints"""

from fastapi import APIRouter, HTTPException, Depends, status
from typing import List, Optional

# Import API models
from ..models.member_models import (
    CreateMemberRequest, UpdateMemberRequest, MemberResponse,
    MemberDetailResponse, PayFineRequest, FineResponse
)
from ..models.common import SuccessResponse

# Import application layer (this will need to be adjusted based on your structure)
# For now, we'll use a dependency injection pattern

router = APIRouter(prefix="/api/members", tags=["members"])


# Dependency injection placeholder - in a real app, this would come from a container
async def get_library_service():
    """Dependency to get the library application service"""
    # This would typically be injected from a DI container
    # For now, returning None - will be implemented when we wire everything together
    return None


@router.post("/",
             response_model=MemberResponse,
             status_code=status.HTTP_201_CREATED,
             summary="Register a new library member")
async def register_member(
    request: CreateMemberRequest,
    service = Depends(get_library_service)
):
    """
    Register a new library member with the provided information.

    - **name**: Member's full name (required)
    - **email**: Valid email address (required)
    - **member_type**: Type of membership (REGULAR, PREMIUM, STUDENT)
    - **phone**: Optional phone number

    Returns the created member information including library card details.
    """
    # Convert API model to application DTO
    from ...application.dtos import RegisterMemberRequest as AppRequest

    app_request = AppRequest(
        name=request.name,
        email=str(request.email),
        member_type=request.member_type.value,
        phone=request.phone
    )

    # Call application service
    result = await service.register_member(app_request)

    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.message
        )

    # Convert to API response model
    return MemberResponse(
        member_id=result.member_id,
        name=request.name,
        email=str(request.email),
        member_type=request.member_type.value,
        library_card_number=result.library_card_number,
        member_since=datetime.now()  # This should come from the domain
    )


@router.get("/{member_id}",
            response_model=MemberDetailResponse,
            summary="Get member details")
async def get_member_details(
    member_id: str,
    service = Depends(get_library_service)
):
    """
    Get detailed information about a library member.

    Returns member information including:
    - Basic details (name, email, type)
    - Library card information
    - Current borrowing status
    - Outstanding fines
    """
    member_details = await service.get_member_details(member_id)

    if not member_details:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found"
        )

    return MemberDetailResponse(
        member_id=member_details.member_id,
        name=member_details.name,
        email=member_details.email,
        member_type=member_details.member_type,
        library_card_number=member_details.library_card_number,
        member_since=member_details.member_since,
        active_loans_count=member_details.active_loans_count,
        total_unpaid_fines=member_details.total_unpaid_fines,
        borrowing_capacity=5 - member_details.active_loans_count,  # This should come from domain service
        library_card_valid=True  # This should be calculated
    )


@router.put("/{member_id}",
            response_model=MemberResponse,
            summary="Update member information")
async def update_member(
    member_id: str,
    request: UpdateMemberRequest,
    service = Depends(get_library_service)
):
    """
    Update member information.

    - **name**: Updated name (optional)
    - **phone**: Updated phone number (optional)
    - **member_type**: Updated membership type (optional)

    Note: Email cannot be updated through this endpoint for security reasons.
    """
    # This would call an update method in the application service
    # For now, returning a placeholder response
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Member update not implemented yet"
    )


@router.delete("/{member_id}",
               status_code=status.HTTP_204_NO_CONTENT,
               summary="Delete a member")
async def delete_member(
    member_id: str,
    service = Depends(get_library_service)
):
    """
    Delete a library member.

    Note: Members with active loans or unpaid fines cannot be deleted.
    """
    # This would call a delete method in the application service
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Member deletion not implemented yet"
    )


@router.get("/{member_id}/fines",
            response_model=List[FineResponse],
            summary="Get member's fines")
async def get_member_fines(
    member_id: str,
    include_paid: bool = False,
    service = Depends(get_library_service)
):
    """
    Get all fines for a member.

    - **include_paid**: Whether to include already paid fines (default: false)
    """
    # This would get fines from the member aggregate
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Get fines not implemented yet"
    )


@router.post("/{member_id}/fines/pay",
             response_model=SuccessResponse,
             summary="Pay member fines")
async def pay_member_fines(
    member_id: str,
    request: PayFineRequest,
    service = Depends(get_library_service)
):
    """
    Pay outstanding fines for a member.

    - **fine_ids**: Specific fine IDs to pay. If not provided, pays all outstanding fines.
    """
    from ...application.dtos import PayFineRequest as AppRequest

    app_request = AppRequest(
        member_id=member_id,
        fine_ids=request.fine_ids
    )

    result = await service.pay_fines(app_request)

    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.message
        )

    return SuccessResponse(
        message=result.message,
        data={
            "total_paid": result.total_paid,
            "remaining_balance": result.remaining_balance
        }
    )


@router.get("/{member_id}/loans",
            summary="Get member's loan history")
async def get_member_loan_history(
    member_id: str,
    active_only: bool = False,
    service = Depends(get_library_service)
):
    """
    Get borrowing history for a member.

    - **active_only**: Whether to show only active loans (default: false)
    """
    loan_history = await service.get_member_loan_history(member_id)

    if active_only:
        loan_history = [loan for loan in loan_history if loan.status == "ACTIVE"]

    return {
        "member_id": member_id,
        "loans": loan_history,
        "total_count": len(loan_history)
    }


@router.get("/",
            response_model=List[MemberResponse],
            summary="Search members")
async def search_members(
    name: Optional[str] = None,
    email: Optional[str] = None,
    member_type: Optional[str] = None,
    page: int = 1,
    limit: int = 50,
    service = Depends(get_library_service)
):
    """
    Search members with optional filters.

    - **name**: Filter by name (partial match)
    - **email**: Filter by email (partial match)
    - **member_type**: Filter by membership type
    - **page**: Page number for pagination
    - **limit**: Number of results per page
    """
    # This would call a search method in the application service
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Member search not implemented yet"
    )