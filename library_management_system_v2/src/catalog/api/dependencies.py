"""DI provider for the Catalog subdomain — reaches the composition root.

`lru_cache` gives one shared CatalogService (so the in-memory store persists
across requests). With a real DB you'd build a fresh service per request
(request-scoped session); only this provider changes, not the controllers.
"""

from functools import lru_cache

from catalog.application.catalog_service import CatalogService
from catalog.infrastructure.inmemory_book_repo import InMemoryBookRepository
from catalog.infrastructure.inmemory_bookcopy_repo import InMemoryBookCopyRepository


@lru_cache
def get_catalog_service() -> CatalogService:
    return CatalogService(InMemoryBookRepository(), InMemoryBookCopyRepository())
