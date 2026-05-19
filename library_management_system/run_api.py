"""
Simple script to run the FastAPI server for testing
"""

import sys
import os
sys.path.append('src')

try:
    from api.main import app
    print("✓ Successfully imported FastAPI app")
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Creating a minimal test API...")

    from fastapi import FastAPI

    app = FastAPI(
        title="Library Management System API",
        description="DDD-based Library Management System",
        version="1.0.0"
    )

    @app.get("/")
    async def root():
        return {
            "message": "Library Management System API",
            "status": "Development mode",
            "architecture": "Domain Driven Design",
            "layers": [
                "API Layer (FastAPI)",
                "Application Services",
                "Domain Services",
                "Domain Entities",
                "Repository Pattern"
            ]
        }

    @app.get("/health")
    async def health_check():
        return {"status": "healthy", "service": "library-api"}

    @app.get("/api/test")
    async def test_endpoint():
        return {
            "message": "API is working!",
            "next_steps": [
                "Wire up dependency injection",
                "Connect to database",
                "Add authentication",
                "Deploy to production"
            ]
        }

    print("✓ Created minimal test API")


if __name__ == "__main__":
    import uvicorn

    print("""
🚀 Starting Library Management System API Server...

🏗️ DDD Architecture:
   📦 API Layer: FastAPI with OpenAPI docs
   📦 Application Layer: Use case orchestration
   📦 Domain Layer: Business logic and rules
   📦 Repository Layer: Data access abstraction

📚 Available endpoints:
   • GET /          - API information
   • GET /health    - Health check
   • GET /docs      - Interactive API documentation
   • GET /api/test  - Test endpoint

🌐 Server will be available at:
   • Main API: http://localhost:8000
   • Docs: http://localhost:8000/docs
   • ReDoc: http://localhost:8000/redoc
    """)

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )