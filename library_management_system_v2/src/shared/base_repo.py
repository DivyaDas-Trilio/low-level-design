from abc import ABC, abstractmethod
from typing import Generic, TypeVar

ID = TypeVar("ID")
T = TypeVar("T")


class Repository(ABC, Generic[ID, T]):
    """Collection-like abstraction over ONE aggregate root — the shared kernel base.

    Generic over the id type (ID) and the aggregate type (T), so every subdomain's
    repository inherits get/save without redeclaring them.
    """

    @abstractmethod
    def get(self, id: ID) -> T:
        """Return the aggregate by its id; raise EntityNotFoundError if missing."""
        ...

    @abstractmethod
    def save(self, aggregate: T) -> None:
        """Insert-or-update (upsert) the whole aggregate."""
        ...
