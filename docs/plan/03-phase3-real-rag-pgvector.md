# Phase 3 — Real RAG with pgvector

Read `docs/plan/00-rules.md` first. Corresponds to the original plan's
Phases 6-9, compressed.

## Goal

Replace the toy in-memory vector store with PostgreSQL + pgvector, build
the first true end-to-end RAG pipeline (retrieve → prompt → generate →
cite), and deliberately break it to understand failure modes.

## Concepts to teach

- What pgvector adds over the toy store: a `vector` column type,
  distance operators, and an HNSW index for real ANN search
- Similarity queries + metadata filtering in SQL
- The RAG pipeline end to end:
  `query → embed → vector search → top-K chunks → prompt construction →
  LLM → answer`
- Hallucination and grounding: why an ungrounded LLM will confidently
  invent plausible-sounding wrong answers, and how retrieved context
  reduces (not eliminates) that
- Citation mapping: every claim in the answer should be traceable to a
  specific chunk, not just "trust me"

## Build tasks

1. **Schema.** Create `documents` and `document_chunks` tables (the
   latter with a `vector` column). Migrate the ingestion pipeline from
   Phase 2 to write here instead of the in-memory store.

2. **Endpoints.**
   - `POST /documents` — register a document
   - `POST /documents/{id}/index` — chunk + embed + store
   - `GET /search` — vector similarity search against stored chunks

3. **RAG V1.** Implement manually (no LangChain/LlamaIndex):
   ```
   query_embedding = embed(query)
   chunks = retrieve(query_embedding)
   prompt = build_prompt(query, chunks)
   answer = llm.generate(prompt)
   ```
   Use an LLM API (don't lock to one provider — keep the call behind a
   small interface).

4. **Structured citations.** Response shape:
   ```json
   {
     "answer": "...",
     "sources": [
       {"document_id": "...", "chunk_id": "...", "title": "...", "section": "..."}
     ]
   }
   ```
   Every source in the list must correspond to a chunk that was
   actually retrieved and used in the prompt — no inventing sources.

5. **Failure analysis.** Deliberately construct questions where
   retrieval fails: wrong document retrieved, exact-keyword questions
   that vector search handles poorly, information split across
   multiple chunks, relevant info that never gets retrieved. Document
   each in `docs/rag-failures.md` with: question, expected source,
   retrieved source, why it failed, possible fix. This sets up the
   motivation for Phase 4 (hybrid search exists specifically to fix
   some of these).

## Deliverable

- Postgres + pgvector running (add to `docker-compose.yml`)
- `documents` / `document_chunks` tables, populated from real ingested
  docs
- Working `POST /documents`, `POST /documents/{id}/index`, `GET /search`
- Working `POST /chat` (or similar) returning grounded answers with
  real citations
- `docs/retrieval.md` and `docs/rag-failures.md`

## Explicit non-goals for this phase

- No BM25 or hybrid retrieval yet (Phase 4)
- No reranking yet (Phase 4)
- No live infrastructure tools or agent yet (Phase 5)

## Sample interview questions for this phase

- Why can RAG still hallucinate even with retrieved context in the
  prompt?
- Walk through what happens, end to end, between a user's question
  arriving and an answer with citations being returned.
- Give a concrete example (from your own failure analysis) of a
  question vector search handles badly, and explain why.

Wait for confirmation before moving to
`04-phase4-hybrid-rerank-eval.md`.
