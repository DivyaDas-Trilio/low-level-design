from shared.exceptions import DomainError


class NegativeMoneyError(DomainError):
    """Raised when a Money amount would be negative (I-5)."""


class FineAlreadySettledError(DomainError):
    """Raised when settling a fine that is already paid or waived."""
