# CloudPilot

**Production-oriented AI infrastructure troubleshooting platform** combining
hybrid RAG, reranking, agentic tool-calling, Kubernetes telemetry, and
retrieval evaluation.

This is a learning project built incrementally, not a framework dump. See
`docs/plan/00-rules.md` for how it's meant to be built, and `docs/plan/`
for the phase-by-phase specification. `docs/architecture.md` has the
problem statement and system design.

## Status

Phase 2 of 7 — retrieval fundamentals, by hand. Embedding service,
cosine similarity computed manually, a brute-force in-memory vector
store, two chunking strategies and an ingestion pipeline that produces
chunks with citation metadata. No vector database yet on purpose —
pgvector arrives in Phase 3. See `docs/plan/02-phase2-retrieval-fundamentals.md`.

Write-ups with the measured results: `docs/embeddings.md`,
`docs/chunking.md`.

## Experiments

```bash
python scripts/embedding_experiment.py    # cosine similarity, by hand
python scripts/chunking_comparison.py     # fixed-size vs heading-aware retrieval

python tests/test_vector_store.py         # or: pytest tests/
python tests/test_chunking.py
```

The first run downloads the embedding model (~90MB) into the Hugging
Face cache.

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
├── services/     # embeddings, chunking, ingestion, vector store
└── repositories/ # data-access layer (empty until later phases)
data/docs/        # sample Kubernetes/Ceph/MinIO troubleshooting notes
scripts/          # throwaway experiments, not part of the app
tests/            # plain-assert tests, runnable with python or pytest
docs/
├── architecture.md   # problem statement + system design
├── embeddings.md     # Phase 2: what the similarity numbers mean
├── chunking.md       # Phase 2: fixed-size vs heading-aware, measured
└── plan/              # phase-by-phase build spec, feed these to Claude Code
```
