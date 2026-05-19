"""Member-related API models"""

from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional, List
from enum import Enum


class MemberTypeEnum(str, Enum):
    REGULAR = "REGULAR"
    PREMIUM = "PREMIUM"
    STUDENT = "STUDENT"


class CreateMemberRequest(BaseModel):
    """Request model for creating a new member"""
    name: str = Field(..., min_length=1, max_length=100, description="Member's full name")
    email: EmailStr = Field(..., description="Valid email address")
    member_type: MemberTypeEnum = Field(default=MemberTypeEnum.REGULAR, description="Membership type")
    phone: Optional[str] = Field(None, max_length=20, description="Phone number")


class UpdateMemberRequest(BaseModel):
    """Request model for updating member information"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    member_type: Optional[MemberTypeEnum] = None


class MemberResponse(BaseModel):
    """Basic member response model"""
    member_id: str
    name: str
    email: str
    member_type: str
    library_card_number: str
    member_since: datetime

    class Config:
        from_attributes = True


class MemberDetailResponse(MemberResponse):
    """Detailed member response with borrowing info"""
    active_loans_count: int
    total_unpaid_fines: float
    borrowing_capacity: int
    library_card_valid: bool


class FineResponse(BaseModel):
    """Fine information response"""
    fine_id: str
    amount: float
    reason: str
    is_paid: bool
    created_date: datetime
    paid_date: Optional[datetime] = None


class PayFineRequest(BaseModel):
    """Request to pay specific fines"""
    fine_ids: Optional[List[str]] = Field(None, description="Specific fine IDs to pay. If null, pays all fines")


class MemberStatsResponse(BaseModel):
    """Member statistics response"""
    total_books_borrowed: int
    current_active_loans: int
    total_fines_paid: float
    total_overdue_incidents: int