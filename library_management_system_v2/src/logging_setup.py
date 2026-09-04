"""Structured logging to STDOUT (12-Factor XI) — the app never manages log files.

The app writes a stream of events to stdout; the platform (Docker / k8s) captures,
routes, and stores them. Logs are JSON so they are QUERYABLE ("every
BorrowingLimitExceededError for member X in the last hour"), not a free-text
graveyard. Deliberately stdlib-only — no extra dependency (structlog would be a
drop-in upgrade later).
"""
import json
import logging
import sys
from datetime import datetime, timezone


class JsonFormatter(logging.Formatter):
    """Render each record as one JSON object per line."""

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname.lower(),
            "event": record.getMessage(),
            "logger": record.name,
        }
        payload.update(getattr(record, "context", {}))   # structured key/values
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        return json.dumps(payload)


def configure_logging(level: str = "INFO") -> None:
    """Point the root logger at stdout with the JSON formatter."""
    handler = logging.StreamHandler(sys.stdout)          # → stdout, never a file
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level.upper())


def log_event(logger: logging.Logger, event: str, **context) -> None:
    """`logger.info(event)` but carrying structured fields → queryable JSON.

        log_event(log, "loan.created", loan_id=str(loan.id), member_id=str(mid))
    """
    logger.info(event, extra={"context": context})
