"""Composition root + demo harness — drives the use cases directly.

No web framework, no database: in-memory repos wired here, use cases called
directly. Run with:  python src/main.py
"""

from shared.exceptions import DomainError
from catalog.application.catalog_service import CatalogService
from catalog.infrastructure.inmemory_book_repo import InMemoryBookRepository
from catalog.infrastructure.inmemory_bookcopy_repo import InMemoryBookCopyRepository


# ---------- composition root: the one place that picks concrete implementations ----------
def build_catalog_service() -> CatalogService:
    return CatalogService(InMemoryBookRepository(), InMemoryBookCopyRepository())


# ---------- demo ----------
def demo_catalog() -> None:
    catalog = build_catalog_service()
    print("=== Catalog subdomain demo ===")

    # UC-9: add a book + copies
    book_id = catalog.add_book("978-0-13-468599-1", "Clean Code", "Robert Martin", "Tech")
    c1 = catalog.add_copy(book_id)
    catalog.add_copy(book_id)
    catalog.add_copy(book_id)
    print(f"UC-9  added book {book_id} with 3 copies")

    # UC-3: availability
    print(f"UC-3  available copies: {catalog.count_available(book_id)}")          # 3

    # UC-8: mark one lost
    catalog.mark_copy_lost(c1)
    print(f"UC-8  marked 1 copy LOST -> available: {catalog.count_available(book_id)}")  # 2

    # UC-7: search
    hits = catalog.search_books("clean")
    print(f"UC-7  search 'clean': {[b.title for b in hits]}")

    # UC-9: update metadata
    catalog.update_book(book_id, title="Clean Code 2e", genre="Software")
    print(f"UC-9  updated title:  {catalog.search_books('clean')[0].title}")

    # UC-9: remove a copy
    catalog.remove_copy(c1)   # already lost; removing it from the catalog
    print(f"UC-9  removed a copy -> available: {catalog.count_available(book_id)}")


def main() -> None:
    try:
        demo_catalog()
    except DomainError as e:                        # handle at the edge, in ONE place
        print(f"Error: {type(e).__name__}: {e}")


if __name__ == "__main__":
    main()
