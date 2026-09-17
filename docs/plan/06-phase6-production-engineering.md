# Phase 6 — Production Engineering

Read `docs/plan/00-rules.md` first. Corresponds to the original plan's
Phases 21-26, compressed. This is the phase that separates "a project
that works on my machine" from "a project I could defend as
production-minded in an interview."

## Concepts to teach

- Observability: what to trace in a RAG pipeline and why (per-stage
  latency, retrieved chunks, reranker scores, token usage) — the
  difference between logging and tracing
- Caching: which layers of a RAG pipeline actually benefit from caching
  (embeddings, repeated retrieval, repeated questions) and where
  caching everything would be wrong (cache invalidation cost, stale
  answers)
- Background processing: why document ingestion shouldn't block the
  API request — queues, workers, retries, idempotency
- Incremental indexing: why re-embedding the entire corpus on every
  document change doesn't scale, and how to detect and re-index only
  what changed
- Authorization at retrieval time: why filtering *after* the LLM
  already saw unauthorized content is a real security bug, not just
  inefficiency

## Build tasks

1. **Observability.** Instrument the RAG pipeline with per-stage timing
   (embedding, vector search, BM25, RRF, reranker, LLM) plus a
   request ID, and produce a trace-style breakdown per request. Use
   OpenTelemetry/Prometheus where it genuinely helps — don't add
   infrastructure for its own sake.

2. **Caching.** Add Redis for at least one clearly justified case
   (e.g. repeated embedding of identical text). Explain and document
   why the other candidate areas were or weren't cached.

3. **Background ingestion.** Move document ingestion off the request
   path: `upload → API enqueues job → worker parses/chunks/embeds/
   stores`. Handle retries and idempotency (re-running a job shouldn't
   duplicate chunks).

4. **Incremental indexing.** When a document changes, re-index only the
   affected chunks, not the whole corpus. Handle versioning, deleted
   documents, and duplicate detection.

5. **Auth + authorization.** Add users and enforce document-level
   permissions **at retrieval time** (the query itself should be scoped
   to what the user is allowed to see) — not as a post-hoc filter on
   an already-fully-retrieved set.

6. **API design pass.** Clean up the API surface with proper
   validation, error handling, and pagination:
   ```
   POST   /api/v1/chat
   POST   /api/v1/documents
   GET    /api/v1/documents
   DELETE /api/v1/documents/{id}
   POST   /api/v1/search
   GET    /api/v1/incidents
   GET    /api/v1/infrastructure/pods
   GET    /api/v1/infrastructure/events
   GET    /api/v1/infrastructure/logs
   POST   /api/v1/evaluation/run
   GET    /api/v1/evaluation/results
   ```

## Deliverable

- Per-request trace/breakdown of pipeline stage latencies
- Redis caching for at least one justified case, documented
- Background worker handling ingestion, with retry + idempotency
- Incremental re-indexing on document update
- Authorization enforced at retrieval time, with a test proving a user
  cannot retrieve another user's restricted documents
- Cleaned-up, versioned API surface
- `docs/observability.md`, `docs/scaling.md`

## Explicit non-goals for this phase

- No React dashboard yet (Phase 7)
- No Kubernetes deployment yet (Phase 7)
- No formal security/penetration testing yet (Phase 7)

## Sample interview questions for this phase

- How would you scale document ingestion to 10 million chunks?
- How would you reduce end-to-end RAG latency, and which stage would
  you look at first?
- Why is enforcing authorization at retrieval time different from
  filtering the LLM's output afterward, and why does that difference
  matter?
- What would you cache in a RAG pipeline, and what would you
  deliberately not cache?

Wait for confirmation before moving to
`07-phase7-frontend-deploy-security-portfolio.md`.
