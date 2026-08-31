from dataclasses import dataclass

from catalog.domain.exceptions import InvalidISBNError


@dataclass(frozen=True)
class ISBN:
    value: str

    def __post_init__(self):
        normalized = self.value.replace("-", "").replace(" ", "")
        # Invariant I-6: an ISBN is 10 or 13 digits (last char of ISBN-10 may be 'X')
        if len(normalized) not in (10, 13) or not normalized[:-1].isdigit():
            raise InvalidISBNError(f"Invalid ISBN: {self.value!r}")
        # frozen=True blocks normal assignment, so set via object.__setattr__
        object.__setattr__(self, "value", normalized)
