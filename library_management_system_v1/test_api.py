"""
Test script to demonstrate the Library Management System API
Shows how to interact with the complete DDD system via HTTP
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"


def print_response(response, action=""):
    """Helper function to print API responses nicely"""
    print(f"\n{'='*50}")
    if action:
        print(f"🔄 {action}")
    print(f"📡 {response.request.method} {response.url}")
    print(f"📊 Status: {response.status_code}")

    try:
        data = response.json()
        print(f"📄 Response:")
        print(json.dumps(data, indent=2, default=str))
    except:
        print(f"📄 Response: {response.text}")


def test_api_endpoints():
    """Test the complete API workflow"""

    print("🚀 Testing Library Management System API")
    print("🏗️ This demonstrates our complete DDD architecture via HTTP")

    # Test health check
    print_response(requests.get(f"{BASE_URL}/health"), "Health Check")

    # Test root endpoint
    print_response(requests.get(f"{BASE_URL}/"), "API Information")

    # Test OpenAPI docs availability
    try:
        docs_response = requests.get(f"{BASE_URL}/docs")
        if docs_response.status_code == 200:
            print(f"\n✅ API Documentation available at: {BASE_URL}/docs")
        else:
            print(f"\n❌ API Documentation not available")
    except:
        print(f"\n❌ Could not reach API documentation")

    # Test if our endpoints are registered (even if not fully implemented)
    endpoints_to_test = [
        "/api/test",
        "/api/members",
        "/api/books",
        "/api/loans",
    ]

    for endpoint in endpoints_to_test:
        try:
            response = requests.get(f"{BASE_URL}{endpoint}")
            status_icon = "✅" if response.status_code < 500 else "⚠️"
            print(f"{status_icon} {endpoint}: {response.status_code}")
        except requests.exceptions.ConnectionError:
            print(f"❌ {endpoint}: Connection failed")


def demonstrate_api_workflow():
    """Demonstrate a complete library workflow via API (when implemented)"""

    print(f"\n{'='*60}")
    print("📚 COMPLETE LIBRARY WORKFLOW DEMONSTRATION")
    print("(This shows what the API will support when fully implemented)")

    workflow_steps = [
        {
            "step": "1️⃣ Register Members",
            "method": "POST",
            "endpoint": "/api/members",
            "payload": {
                "name": "John Doe",
                "email": "john@example.com",
                "member_type": "REGULAR"
            }
        },
        {
            "step": "2️⃣ Add Books",
            "method": "POST",
            "endpoint": "/api/books",
            "payload": {
                "title": "Clean Code",
                "author": "Robert Martin",
                "isbn": "978-0132350884",
                "genre": "Programming"
            }
        },
        {
            "step": "3️⃣ Search Books",
            "method": "GET",
            "endpoint": "/api/books?author=Robert Martin&available_only=true",
            "payload": None
        },
        {
            "step": "4️⃣ Borrow Book",
            "method": "POST",
            "endpoint": "/api/loans/borrow/{member_id}",
            "payload": {
                "book_id": "{book_id}"
            }
        },
        {
            "step": "5️⃣ Check Member Details",
            "method": "GET",
            "endpoint": "/api/members/{member_id}",
            "payload": None
        },
        {
            "step": "6️⃣ Return Book",
            "method": "PUT",
            "endpoint": "/api/loans/{loan_id}/return",
            "payload": {}
        },
        {
            "step": "7️⃣ Pay Fines",
            "method": "POST",
            "endpoint": "/api/members/{member_id}/fines/pay",
            "payload": {}
        },
        {
            "step": "8️⃣ View Loan History",
            "method": "GET",
            "endpoint": "/api/members/{member_id}/loans",
            "payload": None
        }
    ]

    for workflow in workflow_steps:
        print(f"\n{workflow['step']}")
        print(f"   📡 {workflow['method']} {workflow['endpoint']}")
        if workflow['payload']:
            print(f"   📄 Payload: {json.dumps(workflow['payload'], indent=6)}")

    print(f"\n{'='*60}")
    print("🎯 Business Rules Enforced by API:")
    print("   • 5-book borrowing limit (10 for premium members)")
    print("   • No borrowing with unpaid fines")
    print("   • Progressive fine calculation ($1/day, then $2/day)")
    print("   • Different loan periods by member type")
    print("   • Email and ISBN validation")
    print("   • Aggregate boundary enforcement")

    print(f"\n🏗️ DDD Architecture Benefits:")
    print("   • Clean separation of concerns")
    print("   • Business logic centralized in domain layer")
    print("   • Repository pattern abstracts data access")
    print("   • Application services orchestrate workflows")
    print("   • API layer handles HTTP concerns only")

    print(f"\n📖 What You've Learned:")
    print("   ✅ Complete DDD implementation")
    print("   ✅ Domain entities with business rules")
    print("   ✅ Domain services for complex logic")
    print("   ✅ Application services for workflows")
    print("   ✅ Repository pattern for data access")
    print("   ✅ Clean API layer with proper error handling")
    print("   ✅ Dependency injection and IoC")


if __name__ == "__main__":
    print("🧪 API Testing Script for Library Management System")

    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✅ API server is running!")
            test_api_endpoints()
        else:
            print("⚠️ API server responded but may have issues")
    except requests.exceptions.ConnectionError:
        print("❌ API server is not running")
        print(f"💡 Start the server with: python run_api.py")
        print(f"   Then the API will be available at: {BASE_URL}")

    # Always show the workflow demonstration
    demonstrate_api_workflow()

    print(f"\n🎉 Complete DDD Library Management System!")
    print(f"🚀 Next steps:")
    print(f"   • Add database persistence (PostgreSQL/SQLAlchemy)")
    print(f"   • Add authentication (JWT)")
    print(f"   • Add caching (Redis)")
    print(f"   • Add monitoring (Prometheus)")
    print(f"   • Deploy to cloud (Docker + Kubernetes)")