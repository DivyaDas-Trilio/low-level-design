"""FastAPI app assembly — the HTTP entry point (top-level, spans all subdomains).

Run:  uvicorn app:app --app-dir src --reload
Docs: http://127.0.0.1:8000/docs
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from shared.exceptions import DomainError, EntityNotFoundError
from catalog.domain.exceptions import (
    CopyNotAvailableError, CopyNotReturnable, IllegalStatusTransitionError,
)
from catalog.api.controller import router as catalog_router

# specific overrides; any other DomainError falls through to 400
_STATUS = {
    EntityNotFoundError:          404,   # not found
    CopyNotAvailableError:        409,   # conflict
    CopyNotReturnable:            409,
    IllegalStatusTransitionError: 409,
}


def _install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(DomainError)
    async def handle_domain_error(request: Request, exc: DomainError):   # noqa: ANN202
        status = next((code for typ, code in _STATUS.items() if isinstance(exc, typ)), 400)
        return JSONResponse(
            status_code=status,
            content={"error": type(exc).__name__, "detail": str(exc)},
        )


app = FastAPI(title="Library Management System", version="2.0.0")
_install_error_handlers(app)
app.include_router(catalog_router)
# future: app.include_router(lending_router), etc.
