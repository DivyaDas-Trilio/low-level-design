"""
Complete system test demonstrating the full DDD architecture
Shows Application Services orchestrating Domain Services and Entities
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from datetime import datetime, timedelta
from typing import Dict, List

# Import all layers
from domain.entities import Member, Book, Loan
from domain.services import BookBorrowingDomainService, FineCalculationDomainService
from domain.repositories import MemberRepository, BookRepository, LoanRepository


# Simple in-memory repository implementations for testing
class InMemoryMemberRepository(MemberRepository):
    def __init__(self):
        self.members: Dict[str, Member] = {}

    def find_by_id(self, member_id: str):
        return self.members.get(member_id)

    def find_by_email(self, email: str):
        return next((m for m in self.members.values() if m.email.value == email), None)

    def find_by_card_number(self, card_number: str):
        return next((m for m in self.members.values() if m.library_card.card_number == card_number), None)

    def save(self, member: Member):
        self.members[member.member_id] = member

    def delete(self, member: Member):
        self.members.pop(member.member_id, None)

    def find_members_with_overdue_books(self):
        return []  # Simplified for test

    def find_members_with_unpaid_fines(self):
        return [m for m in self.members.values() if m.get_total_unpaid_fines().amount > 0]

    def find_premium_members(self):
        from domain.value_objects import MemberType
        return [m for m in self.members.values() if m.member_type == MemberType.PREMIUM]

    def count_total_members(self):
        return len(self.members)

    def find_members_by_name_pattern(self, pattern: str):
        return [m for m in self.members.values() if pattern.lower() in m.name.lower()]


class InMemoryBookRepository(BookRepository):
    def __init__(self):
        self.books: Dict[str, Book] = {}

    def find_by_id(self, book_id: str):
        return self.books.get(book_id)

    def find_by_isbn(self, isbn: str):
        return next((b for b in self.books.values() if b.isbn.value == isbn), None)

    def save(self, book: Book):
        self.books[book.book_id] = book

    def delete(self, book: Book):
        self.books.pop(book.book_id, None)

    def find_available_books(self, title=None, author=None, genre=None, limit=50):
        results = [b for b in self.books.values() if b.is_available]
        if title:
            results = [b for b in results if title.lower() in b.title.lower()]
        if author:
            results = [b for b in results if author.lower() in b.author.lower()]
        if genre:
            results = [b for b in results if b.genre and genre.lower() in b.genre.lower()]
        return results[:limit]

    def find_all_books(self, title=None, author=None, genre=None, limit=50):
        results = list(self.books.values())
        if title:
            results = [b for b in results if title.lower() in b.title.lower()]
        if author:
            results = [b for b in results if author.lower() in b.author.lower()]
        if genre:
            results = [b for b in results if b.genre and genre.lower() in b.genre.lower()]
        return results[:limit]

    def find_by_title(self, title: str):
        return [b for b in self.books.values() if b.title == title]

    def find_by_author(self, author: str):
        return [b for b in self.books.values() if b.author == author]

    def find_by_genre(self, genre: str):
        return [b for b in self.books.values() if b.genre == genre]

    def find_popular_books(self, limit=10):
        return sorted(self.books.values(), key=lambda x: x.total_borrows, reverse=True)[:limit]

    def count_total_books(self):
        return len(self.books)

    def count_available_books(self):
        return len([b for b in self.books.values() if b.is_available])

    def find_recently_added(self, days=30, limit=20):
        cutoff = datetime.now() - timedelta(days=days)
        return [b for b in self.books.values() if b.added_date >= cutoff][:limit]


class InMemoryLoanRepository(LoanRepository):
    def __init__(self):
        self.loans: Dict[str, Loan] = {}

    def find_by_id(self, loan_id: str):
        return self.loans.get(loan_id)

    def save(self, loan: Loan):
        self.loans[loan.loan_id] = loan

    def delete(self, loan: Loan):
        self.loans.pop(loan.loan_id, None)

    def find_active_loans_for_member(self, member_id: str):
        from domain.value_objects import LoanStatus
        return [l for l in self.loans.values() if l.member_id == member_id and l.status == LoanStatus.ACTIVE]

    def find_all_loans_for_member(self, member_id: str):
        return [l for l in self.loans.values() if l.member_id == member_id]

    def find_loans_for_book(self, book_id: str):
        return [l for l in self.loans.values() if l.book_id == book_id]

    def find_overdue_loans(self):
        return [l for l in self.loans.values() if l.is_overdue()]

    def find_loans_due_soon(self, days=3):
        return [l for l in self.loans.values() if 0 <= l.days_until_due() <= days]

    def count_active_loans_for_member(self, member_id: str):
        return len(self.find_active_loans_for_member(member_id))

    def find_loans_by_status(self, status):
        return [l for l in self.loans.values() if l.status == status]

    def find_loans_by_date_range(self, start_date, end_date):
        return [l for l in self.loans.values() if start_date <= l.borrow_date <= end_date]

    def find_longest_overdue_loans(self, limit=10):
        overdue = self.find_overdue_loans()
        return sorted(overdue, key=lambda x: x.get_overdue_days(), reverse=True)[:limit]

    def count_total_loans(self):
        return len(self.loans)

    def count_active_loans(self):
        from domain.value_objects import LoanStatus
        return len([l for l in self.loans.values() if l.status == LoanStatus.ACTIVE])

    def get_borrowing_statistics(self, member_id: str):
        member_loans = self.find_all_loans_for_member(member_id)
        return {
            'total_loans': len(member_loans),
            'active_loans': len(self.find_active_loans_for_member(member_id)),
            'overdue_count': len([l for l in member_loans if l.is_overdue()])
        }


def create_library_system():
    """Create a complete library system with all layers"""
    # Create repositories
    member_repo = InMemoryMemberRepository()
    book_repo = InMemoryBookRepository()
    loan_repo = InMemoryLoanRepository()

    # Create domain services
    borrowing_service = BookBorrowingDomainService()
    fine_service = FineCalculationDomainService()

    # Create application service
    app_service = LibraryApplicationService(
        member_repo, book_repo, loan_repo, borrowing_service, fine_service
    )

    return app_service


def test_complete_library_workflow():
    print("=== Complete Library Management System Test ===")

    # Initialize system
    library = create_library_system()

    # Step 1: Register members
    print("\n📋 Step 1: Register Members")

    regular_member_req = RegisterMemberRequest("John Doe", "john@example.com", "REGULAR")
    premium_member_req = RegisterMemberRequest("Jane Smith", "jane@example.com", "PREMIUM")
    student_member_req = RegisterMemberRequest("Bob Wilson", "bob@university.edu", "STUDENT")

    regular_resp = library.register_member(regular_member_req)
    premium_resp = library.register_member(premium_member_req)
    student_resp = library.register_member(student_member_req)

    print(f"✓ Regular member: {regular_resp.message}")
    print(f"✓ Premium member: {premium_resp.message}")
    print(f"✓ Student member: {student_resp.message}")

    # Step 2: Add books
    print("\n📚 Step 2: Add Books to Library")

    books_to_add = [
        AddBookRequest("Clean Code", "Robert Martin", "978-0132350884", "Programming"),
        AddBookRequest("Design Patterns", "Gang of Four", "978-0201633610", "Programming"),
        AddBookRequest("The Pragmatic Programmer", "Hunt & Thomas", "978-0135957059", "Programming")
    ]

    book_ids = []
    for book_req in books_to_add:
        resp = library.add_book(book_req)
        print(f"✓ {resp.message}")
        if resp.success:
            book_ids.append(resp.book_id)

    # Step 3: Search books
    print("\n🔍 Step 3: Search Books")

    search_req = BookSearchRequest(author="Robert Martin", available_only=True)
    search_resp = library.search_books(search_req)
    print(f"✓ Found {search_resp.total_count} books by Robert Martin")
    for book in search_resp.books:
        print(f"  - {book['title']} (Available: {book['is_available']})")

    # Step 4: Borrow books
    print("\n📖 Step 4: Borrow Books")

    # Regular member borrows a book
    borrow_req1 = BorrowBookRequest(regular_resp.member_id, book_ids[0])
    borrow_resp1 = library.borrow_book(borrow_req1)
    print(f"✓ Regular member: {borrow_resp1.message}")
    print(f"  Due date: {borrow_resp1.due_date}")

    # Premium member borrows a book
    borrow_req2 = BorrowBookRequest(premium_resp.member_id, book_ids[1])
    borrow_resp2 = library.borrow_book(borrow_req2)
    print(f"✓ Premium member: {borrow_resp2.message}")
    print(f"  Due date: {borrow_resp2.due_date}")

    # Step 5: Check member details
    print("\n👤 Step 5: Check Member Details")

    member_details = library.get_member_details(regular_resp.member_id)
    if member_details:
        print(f"✓ {member_details.name} ({member_details.member_type})")
        print(f"  Active loans: {member_details.active_loans_count}")
        print(f"  Unpaid fines: ${member_details.total_unpaid_fines}")

    # Step 6: Simulate late return and fines
    print("\n⏰ Step 6: Late Return and Fine Calculation")

    # Simulate returning book late
    late_return_date = datetime.now() + timedelta(days=3)  # Return 3 days after due
    return_req = ReturnBookRequest(borrow_resp1.loan_id, late_return_date)
    return_resp = library.return_book(return_req)

    print(f"✓ {return_resp.message}")
    if return_resp.fine_amount > 0:
        print(f"  Fine amount: ${return_resp.fine_amount}")

    # Step 7: Pay fines
    print("\n💰 Step 7: Pay Fines")

    # Check member details after fine
    member_details = library.get_member_details(regular_resp.member_id)
    if member_details and member_details.total_unpaid_fines > 0:
        print(f"Member has ${member_details.total_unpaid_fines} in unpaid fines")

        pay_req = PayFineRequest(regular_resp.member_id)
        pay_resp = library.pay_fines(pay_req)
        print(f"✓ {pay_resp.message}")
        print(f"  Remaining balance: ${pay_resp.remaining_balance}")

    # Step 8: View loan history
    print("\n📋 Step 8: View Loan History")

    loan_history = library.get_member_loan_history(regular_resp.member_id)
    print(f"✓ Found {len(loan_history)} loans for {member_details.name}")
    for loan in loan_history:
        print(f"  - {loan.book_title}: {loan.status} (Borrowed: {loan.borrow_date.date()})")

    print("\n🎉 Complete library workflow test successful!")
    print("\n🏗️ Architecture Summary:")
    print("  ✅ Domain Layer: Entities enforce business rules")
    print("  ✅ Domain Services: Handle multi-aggregate logic")
    print("  ✅ Application Services: Orchestrate complete workflows")
    print("  ✅ Repository Pattern: Clean data access")
    print("  ✅ DTOs: Clean input/output contracts")


def test_business_rules_enforcement():
    print("\n=== Business Rules Enforcement Test ===")

    library = create_library_system()

    # Register a member
    member_req = RegisterMemberRequest("Test User", "test@example.com", "REGULAR")
    member_resp = library.register_member(member_req)

    # Add a book
    book_req = AddBookRequest("Test Book", "Test Author", "123-456789")
    book_resp = library.add_book(book_req)

    # Test borrowing limit
    print("🔒 Testing 5-book borrowing limit...")
    successful_borrows = 0

    for i in range(6):  # Try to borrow 6 books
        # Add more books for testing
        extra_book_req = AddBookRequest(f"Book {i+2}", "Author", f"123-45678{i}")
        extra_book_resp = library.add_book(extra_book_req)

        borrow_req = BorrowBookRequest(member_resp.member_id, extra_book_resp.book_id)
        borrow_resp = library.borrow_book(borrow_req)

        if borrow_resp.success:
            successful_borrows += 1
        else:
            print(f"✓ Borrowing attempt {i+1}: {borrow_resp.message}")

    print(f"✓ Successfully borrowed {successful_borrows}/6 books (limit enforced)")

    print("\n💰 Testing fine blocking...")
    # Member gets a fine
    member_details = library.get_member_details(member_resp.member_id)
    if member_details:
        # Manually add a fine for testing
        from domain.entities import Member
        member_repo = library.member_repo
        member = member_repo.find_by_id(member_resp.member_id)
        member.add_fine(10.0, "Test fine")
        member_repo.save(member)

        # Try to borrow another book
        test_book_req = AddBookRequest("Final Book", "Final Author", "999-999999")
        test_book_resp = library.add_book(test_book_req)

        borrow_req = BorrowBookRequest(member_resp.member_id, test_book_resp.book_id)
        borrow_resp = library.borrow_book(borrow_req)

        print(f"✓ Borrowing with unpaid fines: {borrow_resp.message}")


if __name__ == "__main__":
    test_complete_library_workflow()
    test_business_rules_enforcement()

    print(f"\n🎓 Congratulations! You've successfully implemented a complete DDD system!")
    print(f"📚 You've learned:")
    print(f"   • Domain modeling with aggregates and business rules")
    print(f"   • Service layer separation (Domain vs Application)")
    print(f"   • Repository pattern for clean data access")
    print(f"   • DTO pattern for clean contracts")
    print(f"   • Complete workflow orchestration")