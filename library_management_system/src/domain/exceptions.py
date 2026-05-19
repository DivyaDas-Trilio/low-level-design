"""Domain exceptions for Library Management System"""

class DomainException(Exception):
    """Base exception for domain layer"""
    pass

class ValidationException(DomainException):
    """Raised when domain validation fails"""
    pass

# Member related exceptions
class InvalidEmailError(ValidationException):
    pass

class InvalidNameError(ValidationException):
    pass

class MemberCannotBorrowError(ValidationException):
    pass

class AlreadyPaidError(ValidationException):
    pass

# Book related exceptions
class InvalidISBNError(ValidationException):
    pass

class InvalidTitleError(ValidationException):
    pass

class BookNotAvailableError(ValidationException):
    pass

# Loan related exceptions
class InvalidBorrowDateError(ValidationException):
    pass

class InvalidLoanPeriodError(ValidationException):
    pass

class LoanAlreadyReturnedError(ValidationException):
    pass

# Fine related exceptions
class InvalidFineAmountError(ValidationException):
    pass

class InvalidReasonError(ValidationException):
    pass