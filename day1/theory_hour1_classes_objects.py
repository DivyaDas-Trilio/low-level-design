"""
Day 1 - Hour 1: Theory - Classes and Objects

Learning Goal: Master class design principles - What belongs in a class,
proper initialization, and method organization.

Timeline:
- 10 min: Concept Review
- 15 min: Bad Example Analysis
- 25 min: Good Example Implementation
- 10 min: Key Takeaways
"""

# ==============================================================================
# BAD EXAMPLE: Poor class design
# Problems: Mixed responsibilities, unclear purpose, god object
# ==============================================================================

class BadUserExample:
    """
    This is a BAD example demonstrating poor class design
    Problems: Too many responsibilities, violates SRP, hard to maintain
    """
    def __init__(self, name, email, age, address, phone):
        self.name = name
        self.email = email
        self.age = age
        self.address = address
        self.phone = phone
        self.login_count = 0
        self.last_login = None
        self.shopping_cart = []
        self.order_history = []
        self.payment_methods = []

    def login(self):
        """Authentication logic"""
        self.login_count += 1
        self.last_login = "2024-01-01"  # Simplified

    def send_email_notification(self):
        """Email sending logic"""
        print(f"Sending email to {self.email}")

    def calculate_shipping_cost(self, items):
        """Business logic for shipping"""
        return len(items) * 5.99

    def process_payment(self, amount):
        """Payment processing logic"""
        print(f"Processing payment of ${amount}")

    def generate_report(self):
        """Report generation"""
        return f"User report for {self.name}"

    def validate_email(self):
        """Validation logic"""
        return "@" in self.email

# Problems with BadUserExample:
# 1. Too many responsibilities (authentication, email, payment, shipping, reports)
# 2. Violates Single Responsibility Principle
# 3. Hard to test, maintain, and extend
# 4. Unclear what a "User" actually represents


# ==============================================================================
# GOOD EXAMPLE: Well-designed classes
# Focus: Single responsibility, clear purpose, proper encapsulation
# ==============================================================================

class User:
    """Represents a user in the system with basic personal information"""

    def __init__(self, name, email, age):
        self.name = name
        self.email = email
        self.age = age
        self._created_at = self._get_current_timestamp()

    def get_display_name(self):
        """Returns formatted display name"""
        return f"{self.name} ({self.email})"

    def is_adult(self):
        """Business rule: determine if user is adult"""
        return self.age >= 18

    def _get_current_timestamp(self):
        """Private helper method"""
        return "2024-01-01"  # Simplified for example

    def __str__(self):
        return f"User: {self.name}"

    def __repr__(self):
        return f"User(name='{self.name}', email='{self.email}', age={self.age})"


class UserSession:
    """Handles user authentication and session management"""

    def __init__(self, user):
        self.user = user
        self.login_count = 0
        self.last_login = None
        self.is_active = False

    def login(self):
        """Handle user login"""
        self.login_count += 1
        self.last_login = self._get_current_timestamp()
        self.is_active = True
        return f"{self.user.name} logged in successfully"

    def logout(self):
        """Handle user logout"""
        self.is_active = False
        return f"{self.user.name} logged out"

    def _get_current_timestamp(self):
        return "2024-01-01"  # Simplified


class EmailService:
    """Handles email operations"""

    @staticmethod
    def send_notification(user, message):
        """Send email notification to user"""
        print(f"Sending email to {user.email}: {message}")
        return True


class UserValidator:
    """Validates user data"""

    @staticmethod
    def validate_email(email):
        """Validate email format"""
        return "@" in email and "." in email

    @staticmethod
    def validate_age(age):
        """Validate age range"""
        return 0 <= age <= 150


# ==============================================================================
# DEMONSTRATION AND TESTING
# ==============================================================================

def demonstrate_good_design():
    """Demonstrate the benefits of good class design"""
    print("=== Demonstrating Good Class Design ===")

    # Create user
    user = User("Alice Johnson", "alice@example.com", 25)
    print(f"Created user: {user}")
    print(f"Display name: {user.get_display_name()}")
    print(f"Is adult: {user.is_adult()}")

    # Handle authentication separately
    session = UserSession(user)
    print(f"Login result: {session.login()}")
    print(f"Session active: {session.is_active}")

    # Handle email separately
    EmailService.send_notification(user, "Welcome to our platform!")

    # Handle validation separately
    email_valid = UserValidator.validate_email(user.email)
    age_valid = UserValidator.validate_age(user.age)
    print(f"Email valid: {email_valid}, Age valid: {age_valid}")

    # Logout
    print(f"Logout result: {session.logout()}")


# ==============================================================================
# KEY TAKEAWAYS
# ==============================================================================

"""
Class Design Principles:

1. Single Purpose - Each class should have one clear responsibility
2. Cohesion - Everything in a class should be related to its purpose
3. Encapsulation - Hide internal implementation details
4. Clear Interface - Public methods should be intuitive and minimal

Good Indicators:
- Can explain the class purpose in one sentence
- Methods are related to the core concept
- Easy to test individual components
- Easy to extend without breaking existing code

Questions to Ask When Designing Classes:
1. What data does this concept need?
2. What actions can this concept perform?
3. What actions can be performed ON this concept?
4. Does this belong in this class or should it be separate?
"""


if __name__ == "__main__":
    demonstrate_good_design()

    print("\n" + "="*50)
    print("REFLECTION QUESTIONS:")
    print("1. Can you explain what each class does in one sentence?")
    print("2. What would happen if we needed to change email sending logic?")
    print("3. How easy would it be to add new validation rules?")
    print("4. What are the benefits of separating UserSession from User?")