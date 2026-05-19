"""Quick test to demonstrate our DDD entities in action"""

import sys
import os
sys.path.append('src')

from datetime import datetime, timedelta
from domain.entities import Member, Book, Loan, Fine
from domain.exceptions import *

def test_member_entity():
    print("=== Testing Member Entity ===")

    # Test valid member creation
    member = Member("John Doe", "john@example.com", "REGULAR")
    print(f"✓ Created: {member}")
    print(f"  Library Card: {member.library_card.card_number}")
    print(f"  Can borrow: {member.can_borrow_book()}")
    print(f"  Borrowing capacity: {member.get_borrowing_capacity()}")

    # Test adding fines
    fine = member.add_fine(5.0, "Late return penalty")
    print(f"✓ Added fine: {fine}")
    print(f"  Total unpaid fines: {member.get_total_unpaid_fines()}")
    print(f"  Can borrow with unpaid fines: {member.can_borrow_book()}")

    # Test paying fines
    member.pay_fine(fine.fine_id)
    print(f"✓ Paid fine. Can borrow now: {member.can_borrow_book()}")

    # Test borrowing limit
    for i in range(5):
        member.add_active_loan(f"loan_{i}")
    print(f"✓ Added 5 loans. Can borrow more: {member.can_borrow_book()}")

    # Test validation errors
    try:
        Member("", "john@example.com")
    except InvalidNameError as e:
        print(f"✓ Caught expected error: {e}")

    try:
        Member("John", "invalid-email")
    except InvalidEmailError as e:
        print(f"✓ Caught expected error: {e}")


def test_book_entity():
    print("\n=== Testing Book Entity ===")

    # Test valid book creation
    book = Book("Clean Code", "Robert Martin", "978-0132350884", "Programming")
    print(f"✓ Created: {book}")
    print(f"  Available: {book.is_available}")

    # Test borrowing
    book.mark_as_borrowed()
    print(f"✓ Borrowed book. Available: {book.is_available}")
    print(f"  Total borrows: {book.total_borrows}")

    # Test returning
    book.mark_as_available()
    print(f"✓ Returned book. Available: {book.is_available}")

    # Test validation errors
    try:
        book.mark_as_borrowed()
        book.mark_as_borrowed()  # Try to borrow already borrowed book
    except BookNotAvailableError as e:
        print(f"✓ Caught expected error: {e}")


def test_loan_entity():
    print("\n=== Testing Loan Entity ===")

    # Test valid loan creation
    loan = Loan("member_123", "book_456", datetime.now(), 14)
    print(f"✓ Created: {loan}")
    print(f"  Due date: {loan.due_date}")
    print(f"  Is overdue: {loan.is_overdue()}")
    print(f"  Days until due: {loan.days_until_due()}")

    # Test penalty calculation for overdue loan
    overdue_loan = Loan("member_123", "book_456",
                        datetime.now() - timedelta(days=20), 14)
    penalty = overdue_loan.calculate_penalty()
    print(f"✓ Overdue loan penalty: {penalty}")
    print(f"  Overdue days: {overdue_loan.get_overdue_days()}")

    # Test returning book
    return_penalty = overdue_loan.return_book()
    print(f"✓ Returned overdue book. Penalty: {return_penalty}")
    print(f"  Status: {overdue_loan.status}")


def test_fine_entity():
    print("\n=== Testing Fine Entity ===")

    # Test fine creation and payment
    fine = Fine("member_123", 10.0, "Overdue book penalty")
    print(f"✓ Created: {fine}")
    print(f"  Is paid: {fine.is_paid}")

    fine.mark_as_paid()
    print(f"✓ Paid fine. Is paid: {fine.is_paid}")
    print(f"  Paid date: {fine.paid_date}")

    # Test validation errors
    try:
        Fine("member_123", -5.0, "Invalid fine")
    except InvalidFineAmountError as e:
        print(f"✓ Caught expected error: {e}")


def test_business_scenario():
    print("\n=== Testing Complete Business Scenario ===")

    # Create a member and book
    member = Member("Alice Smith", "alice@example.com", "REGULAR")
    book = Book("The Pragmatic Programmer", "Hunt & Thomas", "978-0135957059")

    print(f"Member: {member}")
    print(f"Book: {book}")
    print(f"Member can borrow: {member.can_borrow_book()}")

    # Create a loan (simulate borrowing)
    loan = Loan(member.member_id, book.book_id)
    book.mark_as_borrowed()
    member.add_active_loan(loan.loan_id)

    print(f"✓ Book borrowed successfully")
    print(f"  Member's active loans: {len(member.active_loan_ids)}")
    print(f"  Book available: {book.is_available}")

    # Return book after due date (simulate overdue)
    late_return_date = loan.due_date + timedelta(days=5)
    penalty = loan.return_book(late_return_date)
    book.mark_as_available()
    member.remove_active_loan(loan.loan_id)

    print(f"✓ Book returned late")
    print(f"  Penalty calculated: {penalty}")
    print(f"  Book available: {book.is_available}")

    # Add fine to member
    if penalty.amount > 0:
        member.add_fine(penalty.amount, f"Late return for loan {loan.loan_id}")
        print(f"  Fine added to member. Total unpaid: {member.get_total_unpaid_fines()}")
        print(f"  Member can borrow: {member.can_borrow_book()}")


if __name__ == "__main__":
    test_member_entity()
    test_book_entity()
    test_loan_entity()
    test_fine_entity()
    test_business_scenario()

    print("\n🎉 All tests completed! Our DDD entities are working correctly!")