# CloudPilot — Architecture

## Problem Statement

When infrastructure breaks — a Kubernetes deployment stuck in
`CrashLoopBackOff`, a Ceph OSD flapping, a MinIO bucket returning errors —
the person on call typically has to manually:

1. Search internal documentation and runbooks.
2. Search or recall past incidents that looked similar.
3. Inspect the live state of the system (pods, nodes, events).
4. Read through logs looking for the relevant lines.
5. Piece all of that together into a diagnosis.

This is slow, inconsistent (depends on who's on call and what they
remember), and knowledge lives in scattered places: wikis, Slack threads,
tribal memory, old tickets.

## Who is the user

An SRE / DevOps / platform engineer who needs a fast, grounded answer to
"why is X broken and what do I do about it" — grounded meaning the answer
cites where it came from (a doc, a past incident, a log line), not a
plausible-sounding guess.

## What CloudPilot should eventually do

Given a question like *"Why is payment-api stuck in CrashLoopBackOff?"*,
CloudPilot should:

1. Understand the question.
2. Search relevant documentation.
3. Search previous incidents.
4. Inspect current infrastructure state (pods, deployments, nodes).
5. Inspect logs and Kubernetes events.
6. Combine that evidence.
7. Generate a diagnosis with citations back to the sources used.
8. Recommend next steps.

## Why RAG, not just an LLM

An LLM alone has no idea about *this* cluster, *this* incident history, or
*this* documentation — and if asked anyway, it will confidently make
something up. RAG (retrieval-augmented generation) grounds the LLM's
answer in retrieved, real evidence, and lets us cite exactly which
document or log line the answer came from.

## Why agentic RAG, not just RAG

Plain RAG answers questions against static documents. But "why is
payment-api failing" isn't answerable from docs alone — it requires
*looking at the live system* (current pod status, recent events, recent
logs). That means the system needs to decide which tools to call (get pod
status? fetch logs? search docs? search past incidents?) based on the
question, not just embed-and-retrieve against a fixed corpus. That's the
agent's job, introduced in Phase 5.

## Why infrastructure data is different from normal documents

Documentation is relatively static and prose-shaped — a good fit for
semantic embedding search. Logs and live infrastructure state are
different: they're structured, time-ordered, full of exact identifiers
(pod names, error codes) where lexical/keyword matching often beats
semantic search, and they change constantly. CloudPilot needs both
retrieval styles (semantic + lexical) and needs to treat "current state"
(call a tool, get a live answer) differently from "historical knowledge"
(retrieve from an index).

## Proposed architecture (target state)

```
                    React UI
                        |
                        v
                  FastAPI (API layer)
                        |
        +---------------+----------------+
        |               |                |
        v               v                v
   RAG Service    Agent Service   Infrastructure API
        |               |                |
        v               v                v
  Retrieval Layer   Tool Calling    Kubernetes API / Logs / Events
        |
  +-----+-----+
  |           |
  v           v
Vector      BM25
Search    (keyword)
  |           |
  +-----+-----+
        v
   RRF Fusion
        v
    Reranker
        v
  Context Builder
        v
       LLM
        v
 Grounded Answer + Citations
```

Supporting infrastructure: PostgreSQL + pgvector, Redis, background
workers, Docker, Kubernetes, observability (OpenTelemetry/Prometheus).

## Current architecture (Phase 1)

Only the skeleton exists so far:

```
FastAPI app
   |
   +-- GET /                -> service info
   +-- GET /api/v1/health   -> process liveness
   +-- GET /api/v1/health/db -> checks Postgres reachability
   |
   v
PostgreSQL (via SQLAlchemy, no models yet)
```

No retrieval, no embeddings, no LLM calls exist yet — deliberately. See
`docs/plan/01-phase1-foundations.md` onward for what gets added, in what
order, and why.

## What we will build in V1 (end of Phase 3)

A working RAG pipeline: ingest markdown docs, chunk them, embed them,
store in pgvector, retrieve top-K by vector similarity, build a prompt,
call an LLM, return an answer with citations mapped to real chunks.

## What we deliberately will NOT build yet

- No LangChain/LlamaIndex or other RAG framework (Phase 1-4 are all
  hand-rolled so the internals are understood first).
- No hybrid search, reranking, or evaluation (Phase 4).
- No live infrastructure tools or agent (Phase 5).
- No auth, caching, background jobs, or React dashboard (Phases 6-7).
