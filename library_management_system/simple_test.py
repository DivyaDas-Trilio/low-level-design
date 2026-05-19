"""Simplified test of complete DDD architecture"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass

# Import domain layer
from domain.entities import Member, Book, Loan
from domain.services import BookBorrowingDomainService, FineCalculationDomainService
from domain.repositories import MemberRepository, BookRepository, LoanRepository


# Simple DTOs for testing
@dataclass
class BorrowResult:
    success: bool
    loan_id: str
    message: str
    due_date: Optional[datetime] = None


@dataclass
class ReturnResult:
    success: bool
    fine_amount: float
    message: str


# Simple Application Service for testing
class SimpleLibraryService:
    def __init__(self, member_repo, book_repo, loan_repo, borrowing_service, fine_service):
        self.member_repo = member_repo
        self.book_repo = book_repo
        self.loan_repo = loan_repo
        self.borrowing_service = borrowing_service
        self.fine_service = fine_service

    def borrow_book(self, member_id: str, book_id: str) -> BorrowResult:
        member = self.member_repo.find_by_id(member_id)
        book = self.book_repo.find_by_id(book_id)

        if not member or not book:
            return BorrowResult(False, "", "Member or book not found")

        if not self.borrowing_service.can_member_borrow_book(member, book):
            return BorrowResult(False, "", "Cannot borrow book")

        # Create loan
        loan = Loan(member_id, book_id)
        book.mark_as_borrowed()
        member.add_active_loan(loan.loan_id)

        # Save (in real system, this would be transactional)
        self.loan_repo.save(loan)
        self.book_repo.save(book)
        self.member_repo.save(member)

        return BorrowResult(True, loan.loan_id, "Book borrowed successfully", loan.due_date)

    def return_book(self, loan_id: str) -> ReturnResult:
        loan = self.loan_repo.find_by_id(loan_id)
        if not loan:
            return ReturnResult(False, 0.0, "Loan not found")

        member = self.member_repo.find_by_id(loan.member_id)
        book = self.book_repo.find_by_id(loan.book_id)

        if not member or not book:
            return ReturnResult(False, 0.0, "Member or book not found")

        # Calculate fine
        fine_amount = self.fine_service.calculate_overdue_fine(loan, member)

        # Return book
        loan.return_book()
        book.mark_as_available()
        member.remove_active_loan(loan.loan_id)

        if fine_amount.amount > 0:
            member.add_fine(fine_amount.amount, f"Late return for {loan.loan_id}")

        # Save changes
        self.loan_repo.save(loan)
        self.book_repo.save(book)
        self.member_repo.save(member)

        return ReturnResult(True, fine_amount.amount, f"Book returned. Fine: ${fine_amount.amount}")


# Simple in-memory repositories
class SimpleMemoryRepo:
    def __init__(self):
        self.data = {}

    def find_by_id(self, id_val):
        return self.data.get(id_val)

    def save(self, entity):
        if hasattr(entity, 'member_id'):
            self.data[entity.member_id] = entity
        elif hasattr(entity, 'book_id'):
            self.data[entity.book_id] = entity
        elif hasattr(entity, 'loan_id'):
            self.data[entity.loan_id] = entity


def test_complete_workflow():
    print("=== Complete DDD Library System Test ===")

    # Setup repositories
    member_repo = SimpleMemoryRepo()
    book_repo = SimpleMemoryRepo()
    loan_repo = SimpleMemoryRepo()

    # Setup domain services
    borrowing_service = BookBorrowingDomainService()
    fine_service = FineCalculationDomainService()

    # Setup application service
    library = SimpleLibraryService(member_repo, book_repo, loan_repo, borrowing_service, fine_service)

    print("\n🏗️ System Architecture:")
    print("  📦 Domain Layer: Entities + Services")
    print("  📦 Application Layer: Workflow Orchestration")
    print("  📦 Repository Layer: Data Access")

    # Step 1: Create entities
    print("\n📋 Step 1: Create Library Entities")

    member = Member("John Doe", "john@example.com", "REGULAR")
    premium_member = Member("Jane Smith", "jane@example.com", "PREMIUM")
    book1 = Book("Clean Code", "Robert Martin", "978-0132350884", "Programming")
    book2 = Book("Design Patterns", "Gang of Four", "978-0201633610", "Programming")

    # Save entities
    member_repo.save(member)
    member_repo.save(premium_member)
    book_repo.save(book1)
    book_repo.save(book2)

    print(f"✓ Created member: {member.name} ({member.member_type.value})")
    print(f"✓ Created premium member: {premium_member.name}")
    print(f"✓ Created books: {book1.title}, {book2.title}")

    # Step 2: Test borrowing business rules
    print("\n📖 Step 2: Test Borrowing Business Rules")

    print(f"Regular member can borrow: {borrowing_service.can_member_borrow_book(member, book1)}")
    print(f"Regular loan period: {borrowing_service.calculate_loan_period(member.member_type)} days")
    print(f"Premium loan period: {borrowing_service.calculate_loan_period(premium_member.member_type)} days")

    # Step 3: Complete borrowing workflow
    print("\n🔄 Step 3: Complete Borrowing Workflow")

    borrow_result = library.borrow_book(member.member_id, book1.book_id)
    print(f"✓ {borrow_result.message}")
    print(f"  Loan ID: {borrow_result.loan_id}")
    print(f"  Due date: {borrow_result.due_date}")
    print(f"  Member's active loans: {len(member.active_loan_ids)}")
    print(f"  Book available: {book1.is_available}")

    # Step 4: Test late return with fines
    print("\n⏰ Step 4: Test Late Return and Fine Calculation")

    # Simulate overdue by creating a loan with past due date
    overdue_loan = Loan(premium_member.member_id, book2.book_id,
                       datetime.now() - timedelta(days=20), 14)
    book2.mark_as_borrowed()
    premium_member.add_active_loan(overdue_loan.loan_id)
    loan_repo.save(overdue_loan)

    print(f"Created overdue loan (due {overdue_loan.get_overdue_days()} days ago)")

    # Calculate different fines for different member types
    regular_fine = fine_service.calculate_overdue_fine(overdue_loan, member)
    premium_fine = fine_service.calculate_overdue_fine(overdue_loan, premium_member)

    print(f"Fine for regular member: {regular_fine}")
    print(f"Fine for premium member: {premium_fine}")

    # Return the overdue book
    return_result = library.return_book(overdue_loan.loan_id)
    print(f"✓ {return_result.message}")

    # Step 5: Test business rule enforcement
    print("\n🔒 Step 5: Test Business Rule Enforcement")

    # Member with fines can't borrow
    print(f"Premium member unpaid fines: {premium_member.get_total_unpaid_fines()}")
    can_borrow_with_fines = borrowing_service.can_member_borrow_book(premium_member, book1)
    print(f"Can borrow with unpaid fines: {can_borrow_with_fines}")

    # Pay fines and try again
    premium_member.pay_all_fines()
    print(f"After paying fines, can borrow: {borrowing_service.can_member_borrow_book(premium_member, book1)}")

    # Test borrowing limit
    print(f"\nTesting borrowing limits:")
    print(f"Regular member limit: {borrowing_service.calculate_max_borrowing_limit(member)}")
    print(f"Premium member limit: {borrowing_service.calculate_max_borrowing_limit(premium_member)}")

    # Step 6: Demonstrate domain service coordination
    print("\n🎯 Step 6: Domain Services Coordination")

    # Show how application service coordinates domain services
    validation_errors = borrowing_service.validate_borrowing_request(member, book2)
    print(f"Validation for clean member and book: {validation_errors or 'No errors'}")

    # Add some complexity
    member.add_fine(15.0, "Lost book fine")
    validation_errors = borrowing_service.validate_borrowing_request(member, book2)
    print(f"Validation with unpaid fines: {validation_errors}")

    print("\n🎉 Complete DDD Architecture Test Successful!")
    print("\n🎓 What You've Learned:")
    print("  ✅ Domain Entities enforce business invariants")
    print("  ✅ Domain Services handle multi-aggregate logic")
    print("  ✅ Application Services orchestrate workflows")
    print("  ✅ Repository pattern abstracts persistence")
    print("  ✅ Clean separation of concerns across layers")
    print("  ✅ Business rules are centralized and consistent")


if __name__ == "__main__":
    test_complete_workflow()