from shared.ids import BookId, CopyId
from catalog.domain.book import Book
from catalog.domain.bookcopy import BookCopy
from catalog.domain.isbn import ISBN
from catalog.domain.repository.book_repo import BookRepository
from catalog.domain.repository.book_copy_repo import BookCopyRepository


class CatalogService:
    """Application service for the Catalog subdomain — thin CRUD / query orchestration.

    Supporting subdomain: NO domain service (no cross-aggregate business rule).
    Depends on repository INTERFACES (injected); the concretes are wired in the
    composition root. Only touches `catalog` + `shared`.
    """

    def __init__(self, books: BookRepository, copies: BookCopyRepository):
        self._books = books
        self._copies = copies

    # ---------- UC-9: manage books & copies ----------
    def add_book(self, isbn: str, title: str, author: str, genre: str | None = None) -> BookId:
        book = Book(BookId.new(), ISBN(isbn), title, author, genre)   # domain creates + validates
        self._books.save(book)
        return book.id

    def add_copy(self, book_id: BookId) -> CopyId:
        self._books.get(book_id)                        # verify the Book exists (raises if not)
        copy = BookCopy(CopyId.new(), book_id)
        self._copies.save(copy)
        return copy.copy_id

    def update_book(self, book_id: BookId, *, title: str | None = None,
                    genre: str | None = None) -> None:
        book = self._books.get(book_id)                 # load
        book.update_metadata(title=title, genre=genre)  # domain command
        self._books.save(book)                          # save

    def remove_book(self, book_id: BookId) -> None:
        self._books.delete(book_id)

    def remove_copy(self, copy_id: CopyId) -> None:
        self._copies.delete(copy_id)

    # ---------- UC-8: mark a copy damaged / lost (load -> command -> save) ----------
    def mark_copy_damaged(self, copy_id: CopyId) -> None:
        copy = self._copies.get(copy_id)
        copy.mark_damaged()
        self._copies.save(copy)

    def mark_copy_lost(self, copy_id: CopyId) -> None:
        copy = self._copies.get(copy_id)
        copy.mark_lost()
        self._copies.save(copy)

    # ---------- UC-7: search ----------
    def search_books(self, keyword: str) -> list[Book]:
        return self._books.search(keyword)

    # ---------- UC-3: availability (catalog side) ----------
    def list_available_copies(self, book_id: BookId) -> list[BookCopy]:
        return self._copies.find_available_for_book(book_id)

    def count_available(self, book_id: BookId) -> int:
        return len(self._copies.find_available_for_book(book_id))
