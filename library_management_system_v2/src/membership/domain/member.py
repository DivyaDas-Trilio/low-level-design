from shared.ids import MemberId
from membership.domain.enums import MemberStatus
from membership.domain.email import EmailAddress


class Member:
    """A library member. Identity is MemberId; equal by id.

    Owns only member-level facts (active/blocked status, profile). It deliberately
    does NOT know its loans — loans are a separate aggregate, and borrowing
    eligibility ("< 2 active loans") is decided by the BorrowingService (step 9).
    Depends only on the shared kernel; references no other subdomain.
    """

    def __init__(self, member_id: MemberId, name: str, email: EmailAddress):
        self._id = member_id
        self._set_name(name)                 # shared validation with update_profile
        self._email = email                  # already-valid EmailAddress VO
        self._status = MemberStatus.ACTIVE

    # --- identity: entities are equal BY ID, not by attributes ---
    def __eq__(self, other) -> bool:
        return isinstance(other, Member) and self._id == other._id

    def __hash__(self) -> int:
        return hash(self._id)

    # --- queries (CQS): facts, no side effects ---
    @property
    def id(self) -> MemberId:
        return self._id

    @property
    def name(self) -> str:
        return self._name

    @property
    def email(self) -> EmailAddress:
        return self._email

    @property
    def is_active(self) -> bool:
        return self._status is MemberStatus.ACTIVE     # whitelist, not "not blocked"

    # --- commands (CQS): change state, return nothing ---
    def update_profile(self, *, name: str | None = None,
                       email: EmailAddress | None = None) -> None:
        # partial update; None means "leave unchanged". No id/status here (SRP).
        if name is not None:
            self._set_name(name)
        if email is not None:
            self._email = email            # replace the VO, don't mutate

    def block(self) -> None:
        self._status = MemberStatus.BLOCKED

    def unblock(self) -> None:
        self._status = MemberStatus.ACTIVE

    # --- factory: mints the id ---
    @classmethod
    def register(cls, name: str, email: EmailAddress) -> "Member":
        return cls(MemberId.new(), name, email)

    # --- shared validation helper (DRY: used by __init__ AND update_profile) ---
    def _set_name(self, name: str) -> None:
        if not name.strip():
            raise ValueError("Member name cannot be empty")
        self._name = name.strip()
