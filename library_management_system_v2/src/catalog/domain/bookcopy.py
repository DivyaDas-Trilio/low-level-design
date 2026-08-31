from shared.ids import BookId, CopyId

from catalog.domain.enums import CopyStatus
from catalog.domain.exceptions import CopyNotAvailableError, CopyNotReturnable


class BookCopy:
    """A physical copy of a Book — its own aggregate. Identity is CopyId.

    References its Book by book_id (by-ID; Book is a separate aggregate).
    """

    def __init__(self, copy_id: CopyId, book_id: BookId):
        self.copy_id = copy_id
        self.book_id = book_id                          # by-ID ref to the Book aggregate
        self._status: CopyStatus = CopyStatus.AVAILABLE

    # --- identity: entities are equal BY ID ---
    def __eq__(self, other) -> bool:
        return isinstance(other, BookCopy) and self.copy_id == other.copy_id

    def __hash__(self) -> int:
        return hash(self.copy_id)

    # --- queries (CQS): facts, no side effects ---
    @property
    def status(self) -> CopyStatus:
        return self._status

    @property
    def is_available(self) -> bool:
        return self._status is CopyStatus.AVAILABLE

    @property
    def is_visible_to_member(self) -> bool:             # rule #6: hide lost/damaged from members
        return self._status in (CopyStatus.AVAILABLE, CopyStatus.LOANED)

    # --- commands (CQS): change state, return nothing ---
    def issue(self) -> None:
        if self._status is not CopyStatus.AVAILABLE:    # invariant I-2 / I-7
            raise CopyNotAvailableError(str(self.copy_id))
        self._status = CopyStatus.LOANED

    def return_copy(self) -> None:
        if self._status is not CopyStatus.LOANED:
            raise CopyNotReturnable(str(self.copy_id))
        self._status = CopyStatus.AVAILABLE

    def mark_damaged(self) -> None:
        self._status = CopyStatus.DAMAGED

    def mark_lost(self) -> None:
        self._status = CopyStatus.LOST
