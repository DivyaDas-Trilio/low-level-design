"""Health probes (Step 14.6) — the platform's eyes.

TWO distinct endpoints, and the distinction is load-bearing (Step 21):

  LIVENESS   /healthz — "is the process alive?"     cheap, NO dependencies.
  READINESS  /readyz  — "can I serve traffic now?"  checks backing services.

Why two: if liveness checked the DB and the DB blipped, the platform would
RESTART every pod → a restart-loop outage. Liveness must be dependency-free.
Readiness may fail (503) when a dependency is down: the pod stops RECEIVING
traffic but keeps running, ready to recover once the dependency returns.
"""
from fastapi import APIRouter, Response, status

router = APIRouter(tags=["health"])


@router.get("/healthz")
def liveness():
    # No dependencies on purpose — answers only "the process is up".
    return {"status": "ok"}


@router.get("/readyz")
def readiness(response: Response):
    # No external backing service yet (repositories are in-memory). Once the SQL
    # adapter lands (Step 18) this runs a cheap `SELECT 1` and, if the database
    # is unreachable, sets 503 WITHOUT killing the process:
    #
    #     if not db.ping():
    #         response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    #         return {"status": "not-ready", "reason": "database unreachable"}
    return {"status": "ready"}
