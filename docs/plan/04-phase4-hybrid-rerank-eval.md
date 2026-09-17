# Phase 4 — Hybrid Search, Reranking & Evaluation

Read `docs/plan/00-rules.md` first. Corresponds to the original plan's
Phases 10-14, compressed. This phase is what turns "a RAG demo" into
"a retrieval system with measured quality" — treat the evaluation part
as non-optional, not a nice-to-have.

## Concepts to teach

- TF-IDF and BM25 — what lexical/keyword search is doing differently
  from semantic search, and why exact identifiers (e.g. `ceph-osd.12`)
  favor it
- Reciprocal Rank Fusion (RRF): understand the formula before
  implementing it, and why it's a reasonable way to combine two
  differently-scored ranked lists
- Why retrieval and reranking are separate problems: retrieval is fast
  candidate generation over the whole corpus, reranking is expensive
  precise scoring over a small candidate set
- Retrieval evaluation metrics: Recall@K, Precision@K, MRR, context
  recall/precision — what each one actually tells you
- Answer evaluation vs retrieval evaluation: "did we retrieve the right
  information" is a different question from "did the LLM use it
  correctly" — faithfulness, answer relevance, context relevance

## Build tasks

1. **BM25.** Implement lexical search independently from vector search.
   Compare results on identifier-heavy queries vs natural-language
   queries.

2. **Hybrid retrieval.** Combine vector search + BM25 via RRF. Measure
   whether it actually improves results on the failure cases logged in
   `docs/rag-failures.md` from Phase 3 — some should now succeed.

3. **Reranking.** Add a reranking step: retrieve top 20-50 candidates
   via hybrid search, rerank down to top 5, feed those to the LLM.
   Compare vector-only vs hybrid vs hybrid+reranker on the same
   queries.

4. **Retrieval evaluation harness.** Build `evaluation/questions.json`
   with at least 50 hand-written question/expected-source pairs (grow
   toward 100+ over time). Write `scripts/evaluate_retrieval.py` that
   reports Recall@K, Precision@K, and MRR for each retrieval mode
   (vector-only, hybrid, hybrid+reranker) — real numbers, not
   estimates.

5. **Answer evaluation.** Add a lighter-weight pass measuring
   faithfulness and answer relevance for a sample of generated
   answers (this can be LLM-assisted evaluation, but be explicit that
   it's an approximation, not ground truth).

## Deliverable

- Working BM25 search, independent of vector search
- Working hybrid retrieval (RRF) as a selectable mode
- Working reranking stage
- `evaluation/questions.json` + `scripts/evaluate_retrieval.py`,
  producing an actual comparison table (vector vs hybrid vs
  hybrid+reranker) with real Recall@K/Precision@K/MRR numbers
- `docs/hybrid-search.md`, `docs/reranking.md`, `docs/rag-evaluation.md`

## Explicit non-goals for this phase

- No live infrastructure tools, logs, or incidents yet (Phase 5)
- No agent/planner yet (Phase 5)
- No caching, background jobs, or auth yet (Phase 6)

## Sample interview questions for this phase

- Why combine BM25 with vector search instead of picking one?
- Explain RRF in plain terms — what is it actually computing?
- Why retrieve 50 candidates and rerank down to 5 instead of just
  retrieving 5 directly?
- What's the difference between retrieval quality and generation
  quality, and how would you diagnose which one is the bottleneck in a
  bad answer?

Wait for confirmation before moving to
`05-phase5-infra-agentic-rag.md`.
