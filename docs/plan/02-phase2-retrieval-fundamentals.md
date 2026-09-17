# Phase 2 — Retrieval Fundamentals (No Vector DB Yet)

Read `docs/plan/00-rules.md` first. This phase corresponds to the
original plan's Phases 2-5, compressed.

## Goal

Understand what an embedding actually is, build a brute-force vector
search engine by hand, and build the document ingestion + chunking
pipeline that will feed it. No pgvector, no framework — everything in
plain Python first.

## Concepts to teach

**Embeddings**
- What a vector/embedding is, and what "dimensions" means
- Cosine similarity, Euclidean distance, dot product — what each
  measures and when they differ
- Why embeddings capture semantic meaning, and their limitations
  (they don't understand exact identifiers well, they can be fooled by
  surface similarity, etc.)

**Brute-force vector search**
- Query → embed → compare against all stored vectors → sort → top-K
- Time and memory complexity of brute force, and why it stops scaling
- What ANN (approximate nearest neighbor) and HNSW are *conceptually* —
  don't implement HNSW, just understand what problem it solves and why
  we'll reach for pgvector's HNSW index in Phase 3 instead of building
  our own

**Document ingestion & chunking**
- The pipeline: load → clean → extract metadata → chunk → embed → store
- Why metadata (source, title, section) matters for later citation and
  filtering
- Chunking strategies: fixed-size, overlapping, sentence-based,
  paragraph-based, heading-aware — and why chunking is genuinely hard
  (bad chunking → missing context, broken explanations, poor retrieval)

## Build tasks

1. **Embedding experiment.** Take 3 sentences (two related, e.g. "How
   do I restart a Kubernetes pod?" / "Kubernetes pod restart
   procedure", and one unrelated, e.g. "How do I cook pasta?"),
   generate embeddings, and compute cosine similarity by hand in
   Python. Confirm the two related sentences score higher. This is a
   throwaway script (`scripts/embedding_experiment.py`), not part of
   the app.

2. **Toy vector store.** Implement a small Python class that stores
   `(document_id, text, embedding, metadata)` tuples in memory and
   implements `search(query_embedding, top_k)` via cosine similarity,
   nothing else. No persistence, no database.

3. **Ingestion pipeline.** Build the real pipeline against a small set
   of markdown/text docs (start with a handful of Kubernetes /
   Ceph / MinIO troubleshooting notes — can be short, written by the
   user or pulled from real docs they already know). Each resulting
   chunk should carry: `id, document_id, content, source, title,
   section, chunk_index, metadata, created_at`.

4. **Chunking comparison.** Implement at least two chunking strategies
   (e.g. fixed-size and heading-aware) and run the same query against
   both. Show a case where they retrieve different, meaningfully
   different results. Write this up.

## Deliverable

- `scripts/embedding_experiment.py` (or similar) with output showing
  similarity scores
- Toy in-memory vector store with a passing test exercising
  `search(query_embedding, top_k)`
- Working ingestion pipeline that turns real documents into chunks with
  full metadata
- `docs/embeddings.md` and `docs/chunking.md`, each following the
  problem/concept/implementation/tradeoffs/experiment/lessons format
  from the rules file

## Explicit non-goals for this phase

- No pgvector, no Postgres storage of embeddings yet (Phase 3)
- No LLM generation yet — retrieval only
- No BM25/hybrid search yet (Phase 4)

## Sample interview questions for this phase

- What does cosine similarity actually measure, and why not just use
  Euclidean distance?
- Why does brute-force search stop being viable, and roughly at what
  scale?
- Give an example where two different chunking strategies would give a
  RAG system genuinely different (not just cosmetically different)
  answers.

Wait for confirmation before moving to `03-phase3-real-rag-pgvector.md`.
