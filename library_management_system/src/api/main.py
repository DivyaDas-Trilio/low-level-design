"""
FastAPI application for Library Management System
Main entry point for the API layer
"""

from fastapi import FastAPI, status
from fastapi.responses import JSONResponse
import logging

# Import middleware
from .middleware import setup_exception_handlers, setup_cors

# Import routers
from .controllers import member_router, book_router, loan_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """Create and configure the FastAPI application"""

    app = FastAPI(
        title="Library Management System API",
        description="""
        A comprehensive Library Management System built with Domain Driven Design.

        ## Features

        * **Member Management**: Register members, manage library cards, handle fines
        * **Book Catalog**: Add books, search catalog, track availability
        * **Loan Operations**: Borrow/return books, calculate fines, extend loans
        * **Business Rules**: Automatic enforcement of library policies

        ## Architecture

        This API follows Domain Driven Design principles:
        * **Domain Layer**: Core business logic and rules
        * **Application Layer**: Use case orchestration
        * **API Layer**: HTTP interface and request handling

        ## Authentication

        Currently using simple authentication. In production, implement proper JWT or OAuth2.
        """,
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/api/openapi.json"
    )

    # Setup middleware
    setup_cors(app)
    setup_exception_handlers(app)

    # Include routers
    app.include_router(member_router)
    app.include_router(book_router)
    app.include_router(loan_router)

    # Add health check endpoint
    @app.get("/health",
             tags=["health"],
             summary="Health check endpoint")
    async def health_check():
        """Simple health check endpoint"""
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": "healthy",
                "service": "Library Management System API",
                "version": "1.0.0"
            }
        )

    # Add root endpoint
    @app.get("/",
             tags=["root"],
             summary="API information")
    async def root():
        """Root endpoint with API information"""
        return {
            "message": "Welcome to the Library Management System API",
            "version": "1.0.0",
            "docs_url": "/docs",
            "health_check": "/health",
            "endpoints": {
                "members": "/api/members",
                "books": "/api/books",
                "loans": "/api/loans"
            }
        }

    logger.info("FastAPI application created successfully")
    return app


# Create the app instance
app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )