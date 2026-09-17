"""
Database engine and session management.

Why this file exists:
    We keep the SQLAlchemy engine/session setup in one place so every part
    of the app talks to Postgres the same way. Using a synchronous engine
    for now (not async) on purpose -- it is easier to reason about while
    we are still building the fundamentals. We can revisit async I/O once
    the basics are solid (see docs/plan/00-rules.md: no premature complexity).
"""

from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session

from app.core.config import get_settings

settings = get_settings()

# pool_pre_ping checks a connection is alive before handing it out, which
# avoids a class of "server closed the connection" errors after idle time.
engine = create_engine(settings.database_url, pool_pre_ping=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency that yields a DB session and guarantees it is closed
    afterwards, even if the request handler raises an exception.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def session_scope() -> Generator[Session, None, None]:
    """Same idea as get_db, but usable outside of a FastAPI request (e.g. in
    scripts or background jobs)."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_db_connection() -> bool:
    """
    Attempts a trivial query against Postgres and reports whether it
    succeeded. Used by the health endpoint so we can tell the difference
    between "the API process is up" and "the API can actually reach its
    database" -- these are two different failure modes in production.
    """
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
