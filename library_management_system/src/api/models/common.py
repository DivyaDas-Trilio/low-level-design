"""Common API models"""

from pydantic import BaseModel
from typing import Optional, Any


class SuccessResponse(BaseModel):
    """Standard success response"""
    success: bool = True
    message: str
    data: Optional[Any] = None


class ErrorResponse(BaseModel):
    """Standard error response"""
    success: bool = False
    error: str
    details: Optional[str] = None


class PaginationParams(BaseModel):
    """Pagination parameters"""
    page: int = 1
    limit: int = 50

    def get_offset(self) -> int:
        return (self.page - 1) * self.limit


class PaginatedResponse(BaseModel):
    """Paginated response wrapper"""
    items: list
    total_count: int
    page: int
    limit: int
    has_more: bool