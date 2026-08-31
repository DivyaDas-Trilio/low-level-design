"""Shared kernel — the only thing every subdomain is allowed to depend on.

Keep this small and stable: typed IDs + the base exception. A large shared
kernel is what prevents a clean microservice split, so resist adding to it.
"""

from shared.exceptions import DomainException, DomainError
from shared.ids import EntityId, BookId, CopyId, MemberId, LoanId, FineId

__all__ = [
    "DomainException", "DomainError",
    "EntityId", "BookId", "CopyId", "MemberId", "LoanId", "FineId",
]
