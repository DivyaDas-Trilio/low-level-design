from dataclasses import dataclass
from datetime import date, timedelta

from lending.domain.exceptions import InvalidDateRangeError


@dataclass(frozen=True)
class DateRange:
    start: date                  # borrow date
    end: date                    # due date

    def __post_init__(self):
        # Invariant I-4: a loan window must end after it starts
        if self.end < self.start:
            raise InvalidDateRangeError(f"due date {self.end} precedes borrow date {self.start}")

    @classmethod
    def for_loan(cls, borrow_date: date, loan_days: int) -> "DateRange":
        """Factory encoding business rule #2: due = borrow + N days."""
        return cls(borrow_date, borrow_date + timedelta(days=loan_days))

    # --- query: how many days overdue, as of some date (a FACT, not a fine) ---
    def days_overdue(self, as_of: date) -> int:
        return max(0, (as_of - self.end).days)

    def is_overdue(self, as_of: date) -> bool:
        return as_of > self.end
