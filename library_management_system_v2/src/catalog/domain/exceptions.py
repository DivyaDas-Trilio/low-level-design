from shared.exceptions import DomainError


class InvalidISBNError(DomainError):
    """Raised when an ISBN is not 10 or 13 digits (I-6)."""


class CopyNotAvailableError(DomainError):
    """Raised when issuing a copy that isn't AVAILABLE (I-2 / I-7)."""
    
class CopyNotReturnable(DomainError):
    """Error"""


class IllegalStatusTransitionError(DomainError):
    """Raised on an illegal BookCopy status transition."""
    
class EntityNotFound(DomainError):
    ...
