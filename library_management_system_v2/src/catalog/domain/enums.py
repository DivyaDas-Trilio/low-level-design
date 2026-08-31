from enum import Enum


class CopyStatus(Enum):
    AVAILABLE = "available"
    LOANED    = "loaned"
    LOST      = "lost"
    DAMAGED   = "damaged"
