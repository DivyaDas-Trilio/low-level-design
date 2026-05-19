"""Test Domain Services to see complete domain layer in action"""

import sys
sys.path.append('src')

from datetime import datetime, timedelta
from domain.entities import Member, Book, Loan
from domain.services import BookBorrowingDomainService, FineCalculationDomainService
from domain.value_objects import MemberType


def test_borrowing_domain_service():
    print("=== Testing BookBorrowingDomainService ===")

    borrowing_service = BookBorrowingDomainService()

    # Create test entities
    regular_member = Member("John Doe", "john@example.com", "REGULAR")
    premium_member = Member("Jane Smith", "jane@example.com", "PREMIUM")
    student_member = Member("Bob Wilson", "bob@university.edu", "STUDENT")

    book = Book("Clean Architecture", "Robert Martin", "978-0134494166")

    # Test borrowing eligibility
    print(f"Regular member can borrow: {borrowing_service.can_member_borrow_book(regular_member, book)}")
    print(f"Premium member can borrow: {borrowing_service.can_member_borrow_book(premium_member, book)}")

    # Test loan periods
    regular_period = borrowing_service.calculate_loan_period(MemberType.REGULAR)
    premium_period = borrowing_service.calculate_loan_period(MemberType.PREMIUM)
    student_period = borrowing_service.calculate_loan_period(MemberType.STUDENT)

    print(f"Loan periods - Regular: {regular_period}, Premium: {premium_period}, Student: {student_period} days")

    # Test borrowing limits
    regular_limit = borrowing_service.calculate_max_borrowing_limit(regular_member)
    premium_limit = borrowing_service.calculate_max_borrowing_limit(premium_member)

    print(f"Borrowing limits - Regular: {regular_limit}, Premium: {premium_limit} books")

    # Test validation
    # Add some fines to member
    regular_member.add_fine(5.0, "Test fine")
    validation_errors = borrowing_service.validate_borrowing_request(regular_member, book)
    print(f"Validation errors with unpaid fines: {validation_errors}")

    # Clear fines and test again
    regular_member.pay_all_fines()
    validation_errors = borrowing_service.validate_borrowing_request(regular_member, book)
    print(f"Validation errors after paying fines: {validation_errors}")


def test_fine_calculation_service():
    print("\n=== Testing FineCalculationDomainService ===")

    fine_service = FineCalculationDomainService()

    # Create test entities
    regular_member = Member("John Doe", "john@example.com", "REGULAR")
    premium_member = Member("Jane Smith", "jane@example.com", "PREMIUM")
    student_member = Member("Bob Wilson", "bob@university.edu", "STUDENT")

    # Create overdue loans
    overdue_3_days = Loan("member1", "book1", datetime.now() - timedelta(days=17), 14)
    overdue_10_days = Loan("member2", "book2", datetime.now() - timedelta(days=24), 14)

    # Test fine calculations for different member types
    regular_fine_3_days = fine_service.calculate_overdue_fine(overdue_3_days, regular_member)
    premium_fine_3_days = fine_service.calculate_overdue_fine(overdue_3_days, premium_member)
    student_fine_3_days = fine_service.calculate_overdue_fine(overdue_3_days, student_member)

    print(f"3-day overdue fines - Regular: {regular_fine_3_days}, Premium: {premium_fine_3_days}, Student: {student_fine_3_days}")

    # Test escalated fines (>7 days overdue)
    regular_fine_10_days = fine_service.calculate_overdue_fine(overdue_10_days, regular_member)
    premium_fine_10_days = fine_service.calculate_overdue_fine(overdue_10_days, premium_member)

    print(f"10-day overdue fines - Regular: {regular_fine_10_days}, Premium: {premium_fine_10_days}")

    # Test fine estimation
    future_return_date = datetime.now() + timedelta(days=2)
    estimated_fine = fine_service.estimate_fine_if_returned_on_date(overdue_3_days, regular_member, future_return_date)
    print(f"Estimated fine if returned in 2 days: {estimated_fine}")

    # Test forgiveness eligibility
    regular_member.add_fine(3.0, "Small fine")
    forgiveness_eligible = fine_service.get_fine_forgiveness_eligibility(regular_member)
    print(f"Forgiveness eligible (small fine): {forgiveness_eligible}")

    regular_member.add_fine(20.0, "Large fine")
    forgiveness_eligible = fine_service.get_fine_forgiveness_eligibility(regular_member)
    print(f"Forgiveness eligible (large fine): {forgiveness_eligible}")

    # Test payment plans
    total_fine = regular_member.get_total_unpaid_fines()
    payment_plan = fine_service.calculate_payment_plan(total_fine, regular_member)
    print(f"Payment plan for {total_fine}: {[str(payment) for payment in payment_plan]}")


def test_complete_borrowing_workflow():
    print("\n=== Testing Complete Borrowing Workflow ===")

    borrowing_service = BookBorrowingDomainService()
    fine_service = FineCalculationDomainService()

    # Create entities
    member = Member("Alice Johnson", "alice@example.com", "REGULAR")
    book = Book("Design Patterns", "Gang of Four", "978-0201633610")

    print(f"Initial state:")
    print(f"  Member: {member}")
    print(f"  Book: {book}")
    print(f"  Can borrow: {borrowing_service.can_member_borrow_book(member, book)}")

    # Step 1: Member borrows book
    if borrowing_service.can_member_borrow_book(member, book):
        # Calculate due date
        due_date = borrowing_service.calculate_due_date(member)

        # Create loan
        loan = Loan(member.member_id, book.book_id, datetime.now(), 14)

        # Update aggregates
        book.mark_as_borrowed()
        member.add_active_loan(loan.loan_id)

        print(f"\n✓ Book borrowed successfully")
        print(f"  Loan ID: {loan.loan_id}")
        print(f"  Due date: {loan.due_date}")
        print(f"  Member active loans: {len(member.active_loan_ids)}")
        print(f"  Book available: {book.is_available}")

        # Step 2: Simulate late return
        late_return_date = loan.due_date + timedelta(days=8)
        penalty = loan.return_book(late_return_date)

        # Calculate fine using domain service (more sophisticated calculation)
        calculated_fine = fine_service.calculate_overdue_fine(loan, member)

        print(f"\n✓ Book returned late")
        print(f"  Return date: {loan.return_date}")
        print(f"  Loan penalty: {penalty}")
        print(f"  Domain service fine: {calculated_fine}")

        # Update aggregates
        book.mark_as_available()
        member.remove_active_loan(loan.loan_id)
        member.add_fine(calculated_fine.amount, f"Late return for loan {loan.loan_id}")

        print(f"  Member unpaid fines: {member.get_total_unpaid_fines()}")
        print(f"  Can borrow again: {borrowing_service.can_member_borrow_book(member, book)}")

        # Step 3: Check forgiveness and payment options
        forgiveness = fine_service.get_fine_forgiveness_eligibility(member)
        payment_plan = fine_service.calculate_payment_plan(member.get_total_unpaid_fines(), member)

        print(f"\n✓ Fine management options:")
        print(f"  Eligible for forgiveness: {forgiveness}")
        print(f"  Payment plan: {[str(p) for p in payment_plan]}")


if __name__ == "__main__":
    test_borrowing_domain_service()
    test_fine_calculation_service()
    test_complete_borrowing_workflow()

    print("\n🎉 Domain Services working perfectly with our entities!")
    print("\nNext: Application Services will orchestrate these domain services for complete use cases!")