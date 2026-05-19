"""
Dependency injection setup for the API layer
Wires together the complete DDD architecture
"""

from typing import Generator
import logging

# Import all layers (adjust imports based on your structure)
# For now using try/except to handle import issues during development
try:
    from ..domain.services import BookBorrowingDomainService, FineCalculationDomainService
    from ..application.services import LibraryApplicationService
except ImportError:
    # Fallback for testing
    BookBorrowingDomainService = None
    FineCalculationDomainService = None
    LibraryApplicationService = None

logger = logging.getLogger(__name__)


class InMemoryRepositoryContainer:
    """
    Simple in-memory repository container for development/testing
    In production, this would be replaced with proper database repositories
    """

    def __init__(self):
        self._member_data = {}
        self._book_data = {}
        self._loan_data = {}

    def get_member_repository(self):
        """Get member repository instance"""
        return InMemoryMemberRepository(self._member_data)

    def get_book_repository(self):
        """Get book repository instance"""
        return InMemoryBookRepository(self._book_data)

    def get_loan_repository(self):
        """Get loan repository instance"""
        return InMemoryLoanRepository(self._loan_data)


# Simple in-memory repository implementations
class InMemoryMemberRepository:
    def __init__(self, data_store):
        self.data = data_store

    def find_by_id(self, member_id: str):
        return self.data.get(member_id)

    def find_by_email(self, email: str):
        return next((m for m in self.data.values() if hasattr(m, 'email') and m.email.value == email), None)

    def save(self, member):
        self.data[member.member_id] = member

    def delete(self, member):
        self.data.pop(member.member_id, None)

    # Additional methods would be implemented here...
    def find_by_card_number(self, card_number: str): return None
    def find_members_with_overdue_books(self): return []
    def find_members_with_unpaid_fines(self): return []
    def find_premium_members(self): return []
    def count_total_members(self): return len(self.data)
    def find_members_by_name_pattern(self, pattern: str): return []


class InMemoryBookRepository:
    def __init__(self, data_store):
        self.data = data_store

    def find_by_id(self, book_id: str):
        return self.data.get(book_id)

    def find_by_isbn(self, isbn: str):
        return next((b for b in self.data.values() if hasattr(b, 'isbn') and b.isbn.value == isbn), None)

    def save(self, book):
        self.data[book.book_id] = book

    def delete(self, book):
        self.data.pop(book.book_id, None)

    def find_available_books(self, title=None, author=None, genre=None, limit=50):
        results = [b for b in self.data.values() if b.is_available]
        if title:
            results = [b for b in results if title.lower() in b.title.lower()]
        return results[:limit]

    # Additional methods would be implemented here...
    def find_all_books(self, title=None, author=None, genre=None, limit=50): return []
    def find_by_title(self, title: str): return []
    def find_by_author(self, author: str): return []
    def find_by_genre(self, genre: str): return []
    def find_popular_books(self, limit=10): return []
    def count_total_books(self): return len(self.data)
    def count_available_books(self): return 0
    def find_recently_added(self, days=30, limit=20): return []


class InMemoryLoanRepository:
    def __init__(self, data_store):
        self.data = data_store

    def find_by_id(self, loan_id: str):
        return self.data.get(loan_id)

    def save(self, loan):
        self.data[loan.loan_id] = loan

    def delete(self, loan):
        self.data.pop(loan.loan_id, None)

    def find_active_loans_for_member(self, member_id: str):
        return [l for l in self.data.values() if l.member_id == member_id and l.status.value == "ACTIVE"]

    def find_overdue_loans(self):
        return [l for l in self.data.values() if l.is_overdue()]

    # Additional methods would be implemented here...
    def find_all_loans_for_member(self, member_id: str): return []
    def find_loans_for_book(self, book_id: str): return []
    def find_loans_due_soon(self, days=3): return []
    def count_active_loans_for_member(self, member_id: str): return 0
    def find_loans_by_status(self, status): return []
    def find_loans_by_date_range(self, start_date, end_date): return []
    def find_longest_overdue_loans(self, limit=10): return []
    def count_total_loans(self): return len(self.data)
    def count_active_loans(self): return 0
    def get_borrowing_statistics(self, member_id: str): return {}


# Global container instance (in production, use proper DI container)
_container = InMemoryRepositoryContainer()


def get_library_service() -> LibraryApplicationService:
    """
    Dependency injection function to create the library application service
    with all its dependencies wired together
    """
    try:
        # Create repositories
        member_repo = _container.get_member_repository()
        book_repo = _container.get_book_repository()
        loan_repo = _container.get_loan_repository()

        # Create domain services
        borrowing_service = BookBorrowingDomainService()
        fine_service = FineCalculationDomainService()

        # Create application service with all dependencies
        library_service = LibraryApplicationService(
            member_repo=member_repo,
            book_repo=book_repo,
            loan_repo=loan_repo,
            borrowing_service=borrowing_service,
            fine_service=fine_service
        )

        logger.info("Library service created successfully with all dependencies")
        return library_service

    except Exception as e:
        logger.error(f"Failed to create library service: {str(e)}")
        raise


def get_repository_container() -> InMemoryRepositoryContainer:
    """Get the repository container instance"""
    return _container


# For testing purposes - reset all data
def reset_data():
    """Reset all repository data - useful for testing"""
    global _container
    _container = InMemoryRepositoryContainer()
    logger.info("Repository data reset")