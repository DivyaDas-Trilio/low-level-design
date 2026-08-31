from shared.exceptions import DomainError


class InvalidDateRangeError(DomainError):
    """Raised when a date range ends before it starts (I-4)."""


class LoanAlreadyReturnedError(DomainError):
    """Raised when returning a loan that is already returned (I-8)."""


class BorrowingLimitExceededError(DomainError):
    """Raised when a member exceeds the active-loan limit (rule #4)."""
