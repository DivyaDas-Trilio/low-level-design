from shared.ids import FineId, MemberId, LoanId
from fines.domain.enums import FineStatus
from fines.domain.money import Money
from fines.domain.exceptions import FineAlreadySettledError


class Fine:
    """Money owed for a late return.

    Identity is FineId. A Fine is *given* its amount (a Money produced by the
    fine Strategy) — it never calculates the rupees itself. References the
    member who owes it and the loan that caused it BY ID (separate aggregates).
    """

    def __init__(self, fine_id: FineId, member_id: MemberId, loan_id: LoanId,
                 amount: Money, status: FineStatus = FineStatus.UNPAID):
        self.id = fine_id
        self.member_id = member_id            # by-ID ref (step 6)
        self.loan_id = loan_id                # by-ID ref (step 6)
        self._amount = amount                 # already a valid Money (I-5 guaranteed by the VO)
        self._status = status

    # --- identity: entities are equal BY ID, not by attributes ---
    def __eq__(self, other) -> bool:
        return isinstance(other, Fine) and self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)

    # --- queries (CQS): facts, no side effects ---
    @property
    def amount(self) -> Money:
        return self._amount

    @property
    def status(self) -> FineStatus:
        return self._status

    @property
    def is_paid(self) -> bool:
        return self._status is FineStatus.PAID

    # --- commands (CQS): change state, return nothing ---
    def pay(self) -> None:
        self._require_unpaid()
        self._status = FineStatus.PAID

    def waive(self) -> None:
        self._require_unpaid()
        self._status = FineStatus.WAIVED

    def _require_unpaid(self) -> None:
        # Invariant: a fine can only be settled once.
        if self._status is not FineStatus.UNPAID:
            raise FineAlreadySettledError(str(self.id))
