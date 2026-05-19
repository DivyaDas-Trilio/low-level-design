"""Application Services - Orchestrate use cases and coordinate domain logic"""

from datetime import datetime
from typing import List, Optional

from ..domain.entities import Member, Book, Loan
from ..domain.services import BookBorrowingDomainService, FineCalculationDomainService
from ..domain.repositories import MemberRepository, BookRepository, LoanRepository
from ..domain.exceptions import *
from .dtos import *


class LibraryApplicationService:
    """
    Application service that orchestrates library operations
    Coordinates between aggregates and handles complete workflows
    """

    def __init__(self,
                 member_repo: MemberRepository,
                 book_repo: BookRepository,
                 loan_repo: LoanRepository,
                 borrowing_service: BookBorrowingDomainService,
                 fine_service: FineCalculationDomainService):
        self.member_repo = member_repo
        self.book_repo = book_repo
        self.loan_repo = loan_repo
        self.borrowing_service = borrowing_service
        self.fine_service = fine_service

    # Member Management Use Cases
    def register_member(self, request: RegisterMemberRequest) -> RegisterMemberResponse:
        """Complete workflow: Register a new library member"""
        try:
            # Check if member already exists
            existing_member = self.member_repo.find_by_email(request.email)
            if existing_member:
                return RegisterMemberResponse(
                    success=False,
                    member_id="",
                    library_card_number="",
                    message="Member with this email already exists"
                )

            # Create new member (domain handles validation)
            member = Member(request.name, request.email, request.member_type)

            # Save to repository
            self.member_repo.save(member)

            return RegisterMemberResponse(
                success=True,
                member_id=member.member_id,
                library_card_number=member.library_card.card_number,
                message="Member registered successfully"
            )

        except ValidationException as e:
            return RegisterMemberResponse(
                success=False,
                member_id="",
                library_card_number="",
                message=str(e)
            )

    def get_member_details(self, member_id: str) -> Optional[MemberDetailsView]:
        """Get complete member information"""
        member = self.member_repo.find_by_id(member_id)
        if not member:
            return None

        return MemberDetailsView(
            member_id=member.member_id,
            name=member.name,
            email=member.email.value,
            member_type=member.member_type.value,
            library_card_number=member.library_card.card_number,
            active_loans_count=len(member.active_loan_ids),
            total_unpaid_fines=member.get_total_unpaid_fines().amount,
            member_since=member.created_date
        )

    # Book Management Use Cases
    def add_book(self, request: AddBookRequest) -> AddBookResponse:
        """Complete workflow: Add a new book to library"""
        try:
            # Check if book already exists
            existing_book = self.book_repo.find_by_isbn(request.isbn)
            if existing_book:
                return AddBookResponse(
                    success=False,
                    book_id="",
                    message="Book with this ISBN already exists"
                )

            # Create new book
            book = Book(request.title, request.author, request.isbn, request.genre)

            # Save to repository
            self.book_repo.save(book)

            return AddBookResponse(
                success=True,
                book_id=book.book_id,
                message="Book added successfully"
            )

        except ValidationException as e:
            return AddBookResponse(
                success=False,
                book_id="",
                message=str(e)
            )

    def search_books(self, request: BookSearchRequest) -> BookSearchResponse:
        """Search books with filters"""
        if request.available_only:
            books = self.book_repo.find_available_books(
                title=request.title,
                author=request.author,
                genre=request.genre,
                limit=request.limit
            )
        else:
            books = self.book_repo.find_all_books(
                title=request.title,
                author=request.author,
                genre=request.genre,
                limit=request.limit
            )

        book_dicts = []
        for book in books:
            book_dicts.append({
                'book_id': book.book_id,
                'title': book.title,
                'author': book.author,
                'isbn': book.isbn.value,
                'genre': book.genre,
                'is_available': book.is_available,
                'total_borrows': book.total_borrows
            })

        return BookSearchResponse(
            books=book_dicts,
            total_count=len(books),
            has_more=len(books) == request.limit
        )

    # Borrowing Use Cases
    def borrow_book(self, request: BorrowBookRequest) -> BorrowBookResponse:
        """Complete workflow: Member borrows a book"""
        try:
            # Load aggregates
            member = self.member_repo.find_by_id(request.member_id)
            book = self.book_repo.find_by_id(request.book_id)

            if not member:
                return BorrowBookResponse(
                    success=False,
                    loan_id="",
                    due_date=datetime.now(),
                    message="Member not found"
                )

            if not book:
                return BorrowBookResponse(
                    success=False,
                    loan_id="",
                    due_date=datetime.now(),
                    message="Book not found"
                )

            # Apply business rules via domain service
            validation_errors = self.borrowing_service.validate_borrowing_request(member, book)
            if validation_errors:
                return BorrowBookResponse(
                    success=False,
                    loan_id="",
                    due_date=datetime.now(),
                    message="; ".join(validation_errors)
                )

            # Calculate due date via domain service
            due_date = self.borrowing_service.calculate_due_date(member)

            # Create loan
            loan = Loan(member.member_id, book.book_id, datetime.now())

            # Update aggregates
            book.mark_as_borrowed()
            member.add_active_loan(loan.loan_id)

            # Save all changes (transaction boundary)
            self.loan_repo.save(loan)
            self.book_repo.save(book)
            self.member_repo.save(member)

            return BorrowBookResponse(
                success=True,
                loan_id=loan.loan_id,
                due_date=loan.due_date,
                message="Book borrowed successfully"
            )

        except Exception as e:
            return BorrowBookResponse(
                success=False,
                loan_id="",
                due_date=datetime.now(),
                message=f"Error borrowing book: {str(e)}"
            )

    def return_book(self, request: ReturnBookRequest) -> ReturnBookResponse:
        """Complete workflow: Return a book and handle fines"""
        try:
            # Load loan
            loan = self.loan_repo.find_by_id(request.loan_id)
            if not loan:
                return ReturnBookResponse(
                    success=False,
                    return_date=datetime.now(),
                    fine_amount=0.0,
                    message="Loan not found"
                )

            # Load related aggregates
            member = self.member_repo.find_by_id(loan.member_id)
            book = self.book_repo.find_by_id(loan.book_id)

            if not member or not book:
                return ReturnBookResponse(
                    success=False,
                    return_date=datetime.now(),
                    fine_amount=0.0,
                    message="Member or book not found"
                )

            # Calculate fine using domain service
            fine_amount_obj = self.fine_service.calculate_overdue_fine(loan, member)

            # Return the book
            return_penalty = loan.return_book(request.return_date)

            # Update book availability
            book.mark_as_available()

            # Remove from member's active loans
            member.remove_active_loan(loan.loan_id)

            # Add fine if overdue
            if fine_amount_obj.amount > 0:
                member.add_fine(fine_amount_obj.amount, f"Late return for loan {loan.loan_id}")

            # Save all changes
            self.loan_repo.save(loan)
            self.book_repo.save(book)
            self.member_repo.save(member)

            message = "Book returned successfully"
            if fine_amount_obj.amount > 0:
                message += f". Fine of ${fine_amount_obj.amount:.2f} has been added to your account"

            return ReturnBookResponse(
                success=True,
                return_date=loan.return_date,
                fine_amount=fine_amount_obj.amount,
                message=message
            )

        except Exception as e:
            return ReturnBookResponse(
                success=False,
                return_date=datetime.now(),
                fine_amount=0.0,
                message=f"Error returning book: {str(e)}"
            )

    # Fine Management Use Cases
    def pay_fines(self, request: PayFineRequest) -> PayFineResponse:
        """Complete workflow: Pay member fines"""
        try:
            member = self.member_repo.find_by_id(request.member_id)
            if not member:
                return PayFineResponse(
                    success=False,
                    total_paid=0.0,
                    remaining_balance=0.0,
                    message="Member not found"
                )

            if request.fine_ids:
                # Pay specific fines
                total_paid = 0.0
                for fine_id in request.fine_ids:
                    try:
                        fine = next(f for f in member.fines if f.fine_id == fine_id)
                        if not fine.is_paid:
                            total_paid += fine.amount.amount
                            member.pay_fine(fine_id)
                    except (StopIteration, ValueError):
                        continue
            else:
                # Pay all fines
                paid_amount = member.pay_all_fines()
                total_paid = paid_amount.amount

            # Save member
            self.member_repo.save(member)

            remaining_balance = member.get_total_unpaid_fines().amount

            return PayFineResponse(
                success=True,
                total_paid=total_paid,
                remaining_balance=remaining_balance,
                message=f"Successfully paid ${total_paid:.2f} in fines"
            )

        except Exception as e:
            return PayFineResponse(
                success=False,
                total_paid=0.0,
                remaining_balance=0.0,
                message=f"Error paying fines: {str(e)}"
            )

    # Query Use Cases
    def get_member_loan_history(self, member_id: str) -> List[LoanDetailsView]:
        """Get complete loan history for a member"""
        loans = self.loan_repo.find_all_loans_for_member(member_id)
        loan_views = []

        for loan in loans:
            # Get member and book details
            member = self.member_repo.find_by_id(loan.member_id)
            book = self.book_repo.find_by_id(loan.book_id)

            if member and book:
                fine_amount = self.fine_service.calculate_overdue_fine(loan, member).amount

                loan_views.append(LoanDetailsView(
                    loan_id=loan.loan_id,
                    member_id=member.member_id,
                    member_name=member.name,
                    book_id=book.book_id,
                    book_title=book.title,
                    borrow_date=loan.borrow_date,
                    due_date=loan.due_date,
                    return_date=loan.return_date,
                    status=loan.status.value,
                    overdue_days=loan.get_overdue_days(),
                    fine_amount=fine_amount
                ))

        return loan_views

    def get_overdue_loans(self) -> List[LoanDetailsView]:
        """Get all currently overdue loans"""
        overdue_loans = self.loan_repo.find_overdue_loans()
        return self._convert_loans_to_views(overdue_loans)

    def _convert_loans_to_views(self, loans: List[Loan]) -> List[LoanDetailsView]:
        """Helper method to convert loans to view objects"""
        loan_views = []
        for loan in loans:
            member = self.member_repo.find_by_id(loan.member_id)
            book = self.book_repo.find_by_id(loan.book_id)

            if member and book:
                fine_amount = self.fine_service.calculate_overdue_fine(loan, member).amount

                loan_views.append(LoanDetailsView(
                    loan_id=loan.loan_id,
                    member_id=member.member_id,
                    member_name=member.name,
                    book_id=book.book_id,
                    book_title=book.title,
                    borrow_date=loan.borrow_date,
                    due_date=loan.due_date,
                    return_date=loan.return_date,
                    status=loan.status.value,
                    overdue_days=loan.get_overdue_days(),
                    fine_amount=fine_amount
                ))

        return loan_views