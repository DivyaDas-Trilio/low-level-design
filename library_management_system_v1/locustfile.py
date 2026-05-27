from locust import HttpUser, task, between
import random
import uuid

class LibraryUser(HttpUser):
    wait_time = between(1, 3)  # Realistic user pauses
    host = "http://localhost:8001"

    def on_start(self):
        """Called when user starts - like user login"""
        # Check if API is available
        response = self.client.get("/health")
        if response.status_code != 200:
            print("❌ API not available!")

    @task(10)  # 10x weight - most common action
    def browse_books(self):
        """Most users just browse"""
        self.client.get("/api/books", name="Browse Books")

    @task(5)   # 5x weight
    def search_books(self):
        """Search functionality"""
        search_terms = ["test", "python", "clean", "code"]
        term = random.choice(search_terms)
        self.client.get(f"/api/books?title={term}", name="Search Books")

    @task(3)   # 3x weight
    def view_book_details(self):
        """User clicks on specific book"""
        # Simulate viewing book details
        book_id = f"book_{random.randint(1, 100)}"
        self.client.get(f"/api/books/{book_id}", name="View Book Details")

    @task(2)   # 2x weight - less frequent
    def register_member(self):
        """New user registration"""
        user_data = {
            "name": f"Test User {uuid.uuid4().hex[:8]}",
            "email": f"user{uuid.uuid4().hex[:8]}@example.com",
            "member_type": random.choice(["REGULAR", "PREMIUM", "STUDENT"])
        }
        self.client.post("/api/members", json=user_data, name="Register Member")

    @task(1)   # 1x weight - least frequent
    def borrow_book_journey(self):
        """Complete user journey - most complex"""
        with self.client.rename_request("Full Borrow Journey"):
            # Step 1: Register
            member_data = {
                "name": f"Borrower {uuid.uuid4().hex[:6]}",
                "email": f"borrower{uuid.uuid4().hex[:6]}@example.com",
                "member_type": "REGULAR"
            }

            register_response = self.client.post("/api/members", json=member_data)

            if register_response.status_code == 201:
                member_id = register_response.json().get("member_id")

                # Step 2: Search for book
                self.client.get("/api/books?available_only=true")

                # Step 3: Try to borrow (might fail - that's realistic)
                book_data = {
                    "title": f"Book {uuid.uuid4().hex[:6]}",
                    "author": "Test Author",
                    "isbn": f"978{uuid.uuid4().hex[:10]}",
                    "genre": "Fiction"
                }

                book_response = self.client.post("/api/books", json=book_data)

                if book_response.status_code == 201:
                    book_id = book_response.json().get("book_id")

                    # Attempt to borrow
                    borrow_data = {"book_id": book_id}
                    self.client.post(
                        f"/api/loans/borrow/{member_id}",
                        json=borrow_data,
                        name="Borrow Book"
                    )
# Advanced user types
class PowerUser(HttpUser):
    """Heavy API users - like librarians"""
    wait_time = between(0.5, 1.5)  # Faster actions
    weight = 1  # Fewer power users
    host = "http://localhost:8001"

    @task
    def admin_operations(self):
        # Rapid-fire administrative actions
        self.client.get("/api/books/stats")
        self.client.get("/api/loans/overdue")
        self.client.get("/api/members?member_type=PREMIUM")

class MobileUser(HttpUser):
    """Mobile users - slower, more browsing"""
    wait_time = between(2, 8)  # Slower mobile interactions
    weight = 3  # More mobile users
    host = "http://localhost:8001"

    @task
    def mobile_browsing(self):
        # Mobile users mostly browse
        self.client.get("/api/books?limit=10")  # Smaller pages
