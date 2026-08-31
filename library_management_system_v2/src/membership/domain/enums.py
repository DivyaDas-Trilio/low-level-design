from enum import Enum


class MemberStatus(Enum):
    ACTIVE  = "active"
    BLOCKED = "blocked"
    # NOTE: no "unblocked" state — unblocking is an ACTION that returns a
    # member to ACTIVE. A member is either ACTIVE or BLOCKED.
