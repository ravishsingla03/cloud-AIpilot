# CloudPilot

**Production-oriented AI infrastructure troubleshooting platform** combining
hybrid RAG, reranking, agentic tool-calling, Kubernetes telemetry, and
retrieval evaluation.

This is a learning project built incrementally, not a framework dump. See
`docs/plan/00-rules.md` for how it's meant to be built, and `docs/plan/`
for the phase-by-phase specification. `docs/architecture.md` has the
problem statement and system design.

## Status

Phase 1 of 7 — project foundation. A FastAPI backend with health checks,
a Postgres connection, Docker setup, and passing tests. No RAG logic yet
on purpose — see `docs/plan/01-phase1-foundations.md`.

## Local setup (without Docker)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env   # edit if your local Postgres differs

uvicorn app.main:app --reload
```

Visit `http://localhost:8000/docs` for interactive API docs.

## Local setup (with Docker)

```bash
docker compose up --build
```

This starts Postgres and the API together. API will be at
`http://localhost:8000`.

## Endpoints so far

- `GET /` — service info
- `GET /api/v1/health` — process liveness (no DB dependency)
- `GET /api/v1/health/db` — reports whether Postgres is reachable

## Project layout

```
app/
├── api/          # FastAPI routers, versioned (v1/)
├── core/         # config, database engine/session
├── models/       # SQLAlchemy models (empty until Phase 3)
├── services/     # business logic (empty until later phases)
└── repositories/ # data-access layer (empty until later phases)
docs/
├── architecture.md   # problem statement + system design
└── plan/              # phase-by-phase build spec, feed these to Claude Code
```
