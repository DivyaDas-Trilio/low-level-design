from shared.exceptions import DomainError


class InvalidEmailError(DomainError):
    """Exception raised for invalid email in the membership domain."""
    
