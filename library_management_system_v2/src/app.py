"""FastAPI app assembly — the HTTP entry point (top-level, spans all subdomains).

Run (dev):  uvicorn app:app --app-dir src --reload
Run (prod): gunicorn app:app -k uvicorn.workers.UvicornWorker -w $WORKERS -b 0.0.0.0:$PORT
Docs:       http://127.0.0.1:8000/docs
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from config import settings
from logging_setup import configure_logging, log_event
from health import router as health_router
from shared.exceptions import DomainError, EntityNotFoundError
from catalog.domain.exceptions import (
    CopyNotAvailableError, CopyNotReturnable, IllegalStatusTransitionError,
)
from catalog.api.controller import router as catalog_router

log = logging.getLogger("lms.app")

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


@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- startup: boot fast, do no heavy work here (Factor IX: disposability) ---
    configure_logging(settings.log_level)                 # structured logs → stdout (Factor XI)
    log_event(log, "app.startup", version=app.version, log_level=settings.log_level)
    yield
    # --- shutdown (SIGTERM): stop new traffic, drain in-flight, close resources ---
    # (the DB connection pool is disposed here once SQL lands in Step 18)
    log_event(log, "app.shutdown")


app = FastAPI(title="Library Management System", version="2.0.0", lifespan=lifespan)
_install_error_handlers(app)
app.include_router(health_router)     # /healthz (liveness) + /readyz (readiness)
app.include_router(catalog_router)
# future: app.include_router(lending_router), etc.
