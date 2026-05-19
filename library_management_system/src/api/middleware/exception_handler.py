"""Exception handling middleware for API layer"""

from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.status import HTTP_422_UNPROCESSABLE_ENTITY, HTTP_500_INTERNAL_SERVER_ERROR
import logging

# Import domain exceptions (adjust import path as needed)
try:
    from ...domain.exceptions import (
        DomainException, ValidationException,
        InvalidEmailError, InvalidNameError, InvalidISBNError, InvalidTitleError,
        MemberCannotBorrowError, BookNotAvailableError,
        LoanAlreadyReturnedError, AlreadyPaidError,
        InvalidFineAmountError
    )
except ImportError:
    # Fallback for testing without proper module structure
    class DomainException(Exception):
        pass
    class ValidationException(DomainException):
        pass

logger = logging.getLogger(__name__)


def setup_exception_handlers(app):
    """Setup custom exception handlers for the FastAPI app"""

    @app.exception_handler(ValidationException)
    async def validation_exception_handler(request: Request, exc: ValidationException):
        """Handle domain validation exceptions"""
        logger.warning(f"Validation error: {str(exc)}")
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "error": "Validation Error",
                "details": str(exc)
            }
        )

    @app.exception_handler(RequestValidationError)
    async def request_validation_exception_handler(request: Request, exc: RequestValidationError):
        """Handle Pydantic validation errors"""
        logger.warning(f"Request validation error: {exc.errors()}")
        return JSONResponse(
            status_code=HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "success": False,
                "error": "Request Validation Error",
                "details": exc.errors()
            }
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        """Handle standard HTTP exceptions"""
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "error": exc.detail,
                "details": None
            }
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """Handle unexpected exceptions"""
        logger.error(f"Unexpected error: {str(exc)}", exc_info=True)
        return JSONResponse(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "error": "Internal Server Error",
                "details": "An unexpected error occurred. Please try again later."
            }
        )

    # Domain-specific exception mappings
    domain_exception_mappings = {
        # Member exceptions
        "InvalidEmailError": (400, "Invalid email format"),
        "InvalidNameError": (400, "Invalid name"),
        "MemberCannotBorrowError": (400, "Member cannot borrow book"),

        # Book exceptions
        "InvalidISBNError": (400, "Invalid ISBN format"),
        "InvalidTitleError": (400, "Invalid book title"),
        "BookNotAvailableError": (409, "Book is not available"),

        # Loan exceptions
        "LoanAlreadyReturnedError": (409, "Loan has already been returned"),

        # Fine exceptions
        "AlreadyPaidError": (409, "Fine has already been paid"),
        "InvalidFineAmountError": (400, "Invalid fine amount"),
    }

    @app.exception_handler(DomainException)
    async def domain_exception_handler(request: Request, exc: DomainException):
        """Handle all domain exceptions with specific mappings"""
        exception_name = type(exc).__name__

        if exception_name in domain_exception_mappings:
            status_code, error_message = domain_exception_mappings[exception_name]
        else:
            status_code, error_message = 400, "Domain Error"

        logger.warning(f"Domain exception ({exception_name}): {str(exc)}")
        return JSONResponse(
            status_code=status_code,
            content={
                "success": False,
                "error": error_message,
                "details": str(exc)
            }
        )