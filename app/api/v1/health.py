"""
Health check endpoints.

Two separate endpoints on purpose:
    - GET /health           -> "is the process alive at all?"
    - GET /health/db        -> "is the process alive AND can it reach Postgres?"

Separating these matters in production: a Kubernetes liveness probe should
usually hit the first one (don't restart the pod just because the database
is briefly unreachable), while a readiness probe or a debugging session
cares about the second one. We'll wire real liveness/readiness probes in
the Kubernetes deployment phase -- for now, just the two endpoints.
"""

from fastapi import APIRouter

from app.core.database import check_db_connection

router = APIRouter()


@router.get("/health")
def health() -> dict:
    return {"status": "ok"}


@router.get("/health/db")
def health_db() -> dict:
    db_ok = check_db_connection()
    return {
        "status": "ok" if db_ok else "degraded",
        "database": "reachable" if db_ok else "unreachable",
    }
