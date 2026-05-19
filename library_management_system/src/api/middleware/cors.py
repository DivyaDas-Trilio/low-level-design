"""CORS middleware setup"""

from fastapi.middleware.cors import CORSMiddleware


def setup_cors(app, origins=None):
    """Setup CORS middleware for the FastAPI app"""

    if origins is None:
        # Default allowed origins for development
        origins = [
            "http://localhost",
            "http://localhost:3000",  # React dev server
            "http://localhost:8080",  # Vue dev server
            "http://127.0.0.1:8000",  # FastAPI dev server
        ]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
        allow_headers=["*"],
    )