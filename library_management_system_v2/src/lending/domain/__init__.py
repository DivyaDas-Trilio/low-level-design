"""Lending subdomain (core) — Loans and the borrowing lifecycle.

Depends only on the `shared` kernel. Never imports another subdomain's internals.
"""

from lending.domain.exceptions import (
    InvalidDateRangeError, LoanAlreadyReturnedError, BorrowingLimitExceededError,
)
from lending.domain.enums import LoanStatus
from lending.domain.daterange import DateRange
from lending.domain.loan import Loan

__all__ = [
    "InvalidDateRangeError", "LoanAlreadyReturnedError", "BorrowingLimitExceededError",
    "LoanStatus", "DateRange", "Loan",
]
