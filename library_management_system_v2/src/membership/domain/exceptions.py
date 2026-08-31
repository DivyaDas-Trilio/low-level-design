from shared.exceptions import DomainError


class InvalidEmailError(DomainError):
    """Raised when an email address is malformed."""
