from enum import Enum


class FineStatus(Enum):
    UNPAID = "unpaid"
    PAID   = "paid"
    WAIVED = "waived"
