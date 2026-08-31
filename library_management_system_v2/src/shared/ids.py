"""Typed identifiers — the shared kernel.

IDs live here (not inside a subdomain) so that subdomains can reference each
other BY ID without importing each other's internals. This keeps the
dependency graph as: every subdomain -> shared, and NO subdomain -> subdomain,
which is exactly what makes a future microservice split a lift-out.
"""

import uuid
from dataclasses import dataclass


@dataclass(frozen=True)
class EntityId:
    """Base for all typed identifiers. Immutable, value-equal, hashable."""
    value: str

    @classmethod
    def new(cls) -> "EntityId":
        return cls(str(uuid.uuid4()))      # generate a fresh unique id

    def __str__(self) -> str:
        return self.value


class BookId(EntityId): ...
class CopyId(EntityId): ...
class MemberId(EntityId): ...
class LoanId(EntityId): ...
class FineId(EntityId): ...
