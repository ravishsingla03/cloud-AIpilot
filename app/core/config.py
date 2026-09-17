"""
Application configuration.

Why this file exists:
    Hardcoding values like database URLs directly in code makes it impossible
    to run the same code in different environments (local machine, CI,
    Docker, Kubernetes) without editing source. Instead, we read
    configuration from environment variables (optionally loaded from a
    .env file for local dev), and expose them through a single typed
    object that the rest of the app depends on.

This is the first appearance of "dependency injection" in the project:
    Instead of every module reaching out and reading os.environ directly,
    they ask for a Settings object. FastAPI's `Depends()` mechanism (used
    in database.py and the API routes) will hand them one. That makes it
    trivial to swap in different settings during tests.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "CloudPilot"
    app_env: str = "development"
    database_url: str = "postgresql://cloudpilot:cloudpilot@localhost:5432/cloudpilot"

    # Reads from a .env file if present, but real environment variables
    # (e.g. set by Docker/Kubernetes) always take priority.
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    """
    Returns a cached Settings instance.

    lru_cache means Settings() is only constructed once per process, not
    once per request. FastAPI route handlers will call this via Depends(),
    and tests can override it with dependency_overrides.
    """
    return Settings()
