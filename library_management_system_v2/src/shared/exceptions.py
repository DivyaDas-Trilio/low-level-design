"""The base of the domain exception hierarchy — shared kernel.

Every subdomain's specific errors derive from DomainError, so the API layer
can catch the base once and map it to a 400.
"""


class DomainException(Exception):
    """Base class for domain exceptions."""


class DomainError(DomainException):
    """Base class for every domain rule violation."""


class EntityNotFoundError(DomainError):
    """Raised when an aggregate cannot be found by its id (generic, used by every repo)."""
    
class EntityAlreadyExistsError(DomainError):
    """Raised when an aggregate is already present in DB."""
