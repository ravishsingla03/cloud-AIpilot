# Phase 1 — System Design + Project Foundation

Read `docs/plan/00-rules.md` first — it governs how you teach and build
throughout this project.

## Goal

Understand what CloudPilot is and why it's structured the way it is, and
have a clean, working Python backend skeleton with a real database
connection, health checks, Docker, and passing tests.

## Status

**A starter skeleton already exists in this repo.** It was scaffolded
before you were brought in, precisely to this phase's spec, so there
would be something working on day one. Your job now is:

1. Walk through the existing code with the user file by file
   (`app/main.py`, `app/core/config.py`, `app/core/database.py`,
   `app/api/v1/health.py`, `tests/test_health.py`) and make sure they
   actually understand each piece — don't assume it's understood just
   because it exists.
2. Run the tests (`pytest tests/ -v`) and `docker compose up` together
   with the user so they see it working end to end, not just read about
   it.
3. Only after that, treat Phase 1 as "done" and move to Phase 2.

Do not regenerate this code from scratch — extend and explain what's
there. If the user wants to change a design decision (e.g. async vs sync
DB engine), that's a good moment to explain the tradeoff before changing
it.

## Concepts to teach

- What problem does CloudPilot solve, concretely? (see
  `docs/architecture.md` — walk through it with them)
- FastAPI basics: routers, path operations, automatic docs at `/docs`
- Dependency injection: why `get_settings()` and `get_db()` are written
  as functions handed to `Depends()`, not called directly
- Configuration via environment variables vs hardcoding
- SQLAlchemy engine vs session — what each one is responsible for
- Why the health check is split into `/health` (liveness) and
  `/health/db` (readiness-ish) — and why `/health/db` degrades instead
  of crashing when Postgres is unreachable
- Repository/service/model folder separation — even though they're
  empty right now, explain what will eventually live in each and why
  keeping them separate matters as the app grows
- What `pytest` + `TestClient` are doing in `test_health.py`

## What's already built (verify, don't redo)

- FastAPI app (`app/main.py`) with a root endpoint and versioned API
  (`/api/v1/...`)
- `Settings` config object read from environment/`.env`
  (`app/core/config.py`)
- SQLAlchemy engine + session + `check_db_connection()`
  (`app/core/database.py`)
- `GET /health` and `GET /health/db` endpoints
- `Dockerfile` + `docker-compose.yml` (Postgres + app)
- `pytest` suite covering all three endpoints, passing without a live
  database

## Deliverable

- `docs/architecture.md` reviewed and understood (already written —
  read it together, don't skip it)
- Confirm `pytest tests/ -v` passes locally
- Confirm `docker compose up --build` brings up Postgres + the API
  together, and `curl localhost:8000/api/v1/health/db` reports
  `"database": "reachable"`

## Explicit non-goals for this phase

- No embeddings, retrieval, or LLM calls yet
- No document/chunk models yet (empty `app/models/`)
- No frontend
- No auth

## Sample interview questions for this phase

- What's the difference between a liveness probe and a readiness probe,
  and why would you never want the database down to trigger a pod
  restart?
- Why use dependency injection for settings/DB session instead of
  importing a global object everywhere?
- Why separate `api/`, `services/`, and `repositories/` even when two of
  them are currently empty?

Wait for the user to confirm Phase 1 is genuinely understood (not just
"it runs") before moving to `02-phase2-retrieval-fundamentals.md`.
