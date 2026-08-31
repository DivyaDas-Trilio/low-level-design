import re
from dataclasses import dataclass

from membership.domain.exceptions import InvalidEmailError

# Pragmatic check (KISS) — not a full RFC validator: something@something.something
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


@dataclass(frozen=True)
class EmailAddress:
    """A member's email — a value object, valid by construction, stored normalized."""
    value: str

    def __post_init__(self):
        normalized = self.value.strip().lower()
        if not _EMAIL_RE.match(normalized):
            raise InvalidEmailError(f"Invalid email: {self.value!r}")
        # frozen=True blocks normal assignment, so set the cleaned form via object.__setattr__
        object.__setattr__(self, "value", normalized)

    def __str__(self) -> str:
        return self.value
