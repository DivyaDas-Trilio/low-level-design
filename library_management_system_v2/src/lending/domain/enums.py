from enum import Enum


class LoanStatus(Enum):
    ACTIVE    = "active"
    RETURNED  = "returned"
    OVERDUE   = "overdue"
