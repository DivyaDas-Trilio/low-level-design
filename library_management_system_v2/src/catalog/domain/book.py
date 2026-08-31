from shared.ids import BookId
from catalog.domain.isbn import ISBN


class Book:
    """Catalog metadata for an abstract work.

    You never issue a Book — you issue a BookCopy (a separate aggregate).
    Identity is BookId; two Books are equal iff they share that id.
    """

    def __init__(self, book_id: BookId, isbn: ISBN, title: str,
                 author: str, genre: str | None = None):
        # Invariant: title and author must be non-empty (input-shape validation)
        if not title.strip():
            raise ValueError("Book title cannot be empty")
        if not author.strip():
            raise ValueError("Book author cannot be empty")
        self.id = book_id
        self.isbn = isbn                       # already-validated value object
        self.title = title.strip()
        self.author = author.strip()
        self.genre = genre.strip() if genre else None

    # --- identity: entities are equal BY ID, not by attributes ---
    def __eq__(self, other) -> bool:
        return isinstance(other, Book) and self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)

    # --- command (CQS): change state, return nothing ---
    def update_metadata(self, *, title: str | None = None, genre: str | None = None) -> None:
        # Note: ISBN and author identify the work and are intentionally NOT editable here.
        if title is not None:
            if not title.strip():
                raise ValueError("title cannot be empty")
            self.title = title.strip()
        if genre is not None:
            self.genre = genre.strip()

    # --- query (CQS): return a fact, no side effects (supports search, UC-7) ---
    def matches(self, keyword: str) -> bool:
        k = keyword.lower()
        return k in self.title.lower() or k in self.author.lower()
