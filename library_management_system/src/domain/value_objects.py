"""Value objects for Library Management System"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import re
from typing import Optional

class MemberType(Enum):
    REGULAR = "REGULAR"
    PREMIUM = "PREMIUM"
    STUDENT = "STUDENT"

class LoanStatus(Enum):
    ACTIVE = "ACTIVE"
    RETURNED = "RETURNED"
    OVERDUE = "OVERDUE"

@dataclass(frozen=True)
class LibraryCard:
    """Value object representing a library card"""
    card_number: str
    issue_date: datetime
    expiry_date: datetime

    def is_valid(self) -> bool:
        return datetime.now() <= self.expiry_date

@dataclass(frozen=True)
class Email:
    """Value object for email validation"""
    value: str

    def __post_init__(self):
        if not self._is_valid_email(self.value):
            from .exceptions import InvalidEmailError
            raise InvalidEmailError(f"Invalid email format: {self.value}")

    def _is_valid_email(self, email: str) -> bool:
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None

@dataclass(frozen=True)
class ISBN:
    """Value object for ISBN validation"""
    value: str

    def __post_init__(self):
        if not self._is_valid_isbn(self.value):
            from .exceptions import InvalidISBNError
            raise InvalidISBNError(f"Invalid ISBN format: {self.value}")

    def _is_valid_isbn(self, isbn: str) -> bool:
        # Simplified ISBN validation - just check format
        cleaned = isbn.replace('-', '').replace(' ', '')
        return len(cleaned) in [10, 13] and cleaned.isdigit()

@dataclass(frozen=True)
class Money:
    """Value object for monetary amounts"""
    amount: float
    currency: str = "USD"

    def __post_init__(self):
        if self.amount < 0:
            raise ValueError("Money amount cannot be negative")

    def add(self, other: 'Money') -> 'Money':
        if self.currency != other.currency:
            raise ValueError("Cannot add money with different currencies")
        return Money(self.amount + other.amount, self.currency)

    def __str__(self):
        return f"${self.amount:.2f}"