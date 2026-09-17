"""
Application entrypoint.

Run locally with:
    uvicorn app.main:app --reload

This module's only job is to construct the FastAPI app and wire up
routers. Actual logic lives in app/api, app/services, app/repositories --
main.py should stay thin as the project grows.
"""

from fastapi import FastAPI

from app.api.v1 import health
from app.core.config import get_settings

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    description="AI infrastructure troubleshooting platform.",
    version="0.1.0",
)

app.include_router(health.router, prefix="/api/v1", tags=["health"])


@app.get("/")
def root() -> dict:
    return {
        "service": settings.app_name,
        "env": settings.app_env,
        "docs": "/docs",
    }
