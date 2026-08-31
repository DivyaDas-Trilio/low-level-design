from dataclasses import dataclass

from fines.domain.exceptions import NegativeMoneyError


@dataclass(frozen=True)
class Money:
    amount: int                 # store paise/cents as int — NEVER float for money
    currency: str = "INR"

    def __post_init__(self):
        # Invariant I-5: money is never negative
        if self.amount < 0:
            raise NegativeMoneyError(f"Money cannot be negative: {self.amount}")

    # --- factory for readability ---
    @classmethod
    def rupees(cls, rupees: int) -> "Money":
        return cls(rupees * 100)            # ₹5 -> 500 paise

    # --- side-effect-free operations: return NEW Money, never mutate ---
    def add(self, other: "Money") -> "Money":
        self._same_currency(other)
        return Money(self.amount + other.amount, self.currency)

    def multiply(self, factor: int) -> "Money":
        return Money(self.amount * factor, self.currency)

    def _same_currency(self, other: "Money") -> None:
        if self.currency != other.currency:
            raise ValueError("Cannot mix currencies")

    def __str__(self) -> str:
        return f"₹{self.amount / 100:.2f}"
