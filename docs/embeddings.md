# Embeddings

> Phase 2. Code: `app/services/embeddings.py`,
> `app/services/vector_store.py`, `scripts/embedding_experiment.py`.

## The problem

CloudPilot has to answer "why is my pod in CrashLoopBackOff?" from a pile
of runbooks, postmortems and vendor docs. Keyword search fails the moment
the user's words differ from the document's words: the runbook says
"exit code 137", the user says "my pod keeps dying". We need a way to
retrieve text by *meaning*, not by string match — and the computer only
compares numbers, so meaning has to become numbers first.

## The concept

An embedding model maps a piece of text to a fixed-length vector (384
numbers for `all-MiniLM-L6-v2`). It is trained so that texts humans
consider similar land close together in that space, and unrelated texts
land far apart. "Close" is measured by the angle between vectors:

```
cosine(a, b) = dot(a, b) / (|a| * |b|)
```

Cosine ignores magnitude and compares direction only. That matters
because a long document and a short question about it should count as
similar even though one has far more text in it.

The whole of vector search is: embed every chunk once at ingestion time,
embed the query at question time, and return the chunks whose vectors
point most nearly the same way as the query's.

## The alternatives

| Option | Why not (yet) |
|---|---|
| Keyword / BM25 | Exact on rare terms, blind to paraphrase. It is genuinely complementary, not inferior — Phase 4 combines the two. |
| Bigger embedding model (bge-large, e5-large, OpenAI `text-embedding-3`) | Better benchmark scores, but ~10x the size or a per-call bill. Nothing justifies that before we can measure retrieval quality (Phase 4). |
| Fine-tuning our own model | Needs labelled infra queries we do not have. |
| Vector database (pgvector, Qdrant, Pinecone) | Comes in Phase 3. The point of this phase is that the similarity maths is small enough to write by hand. |

## The implementation

`app/services/embeddings.py` owns one model for the whole process. That
is the only real design decision here: vectors from two different models
live in different spaces, and comparing them produces numbers that look
plausible and mean nothing. One module makes that mistake hard.

`app/services/vector_store.py` is the toy store — a list of
`(item, vector, norm)` and a brute-force loop:

```python
scored = (
    (sum(x * y for x, y in zip(query_vector, vector)) / (query_norm * norm), item)
    for item, vector, norm in self._entries
)
return heapq.nlargest(top_k, scored, key=lambda pair: pair[0])
```

That loop *is* a vector database, minus the index, the persistence and
the SQL. It is O(n·d) per query: every stored vector is touched on every
search. At 21 chunks that is free. At 10 million chunks it is the reason
ANN indexes (HNSW, IVFFlat) exist — they trade exact results for
sublinear search.

Run the test: `python tests/test_vector_store.py`

## The experiment

`python scripts/embedding_experiment.py` — seven sentences, cosine and
Euclidean distance computed by hand (`math.hypot`, no numpy, no library
similarity helper).

```
dimensions: 384
  ||v0|| ... ||v6|| = 1.0000   (all seven)

(0,1)  cosine=+0.9369   euclidean=0.3552
(0,2)  cosine=+0.0509   euclidean=1.3777
(0,3)  cosine=+0.1677   euclidean=1.2902
(0,4)  cosine=+0.8049   euclidean=0.6246
(5,6)  cosine=+0.9769   euclidean=0.2148
```

The sentences:

```
0: How do I restart a Kubernetes pod?
1: Kubernetes pod restart procedure
2: How do I cook pasta?
3: terminate and reschedule the workload
4: How do I permanently delete a Kubernetes pod?
5: pod-7f9b4c is crashing
6: pod-7f9b4d is crashing
```

## What the numbers actually say

**(0,1) = 0.9369 — the happy case.** A paraphrase that shares vocabulary
scores very high. This is the case every RAG demo shows.

**(0,2) = 0.0509 — unrelated text is orthogonal, not opposite.** Pasta
does not score -1; it scores ~0. In practice nothing in a real corpus is
negatively similar, so the useful range of cosine is roughly 0 to 1, and
a "similarity threshold" has to be calibrated per model, not guessed.

**(0,3) = 0.1677 — the model missed a true paraphrase.** "Terminate and
reschedule the workload" is what an SRE says when they mean "restart a
pod", and the model scored it barely above pasta. Embeddings capture
*topical vocabulary* far more than intent. Domain jargon that shares no
words with the question is a blind spot, and no amount of top-K tuning
fixes it.

**(0,4) = 0.8049 — the dangerous case.** "Permanently delete a pod" is
the *opposite* intent from "restart a pod", and it scored 0.80 — above
the true paraphrase in (0,3). Vector similarity has no notion of
negation, intent or safety. A retriever that answered "how do I restart
a pod" with the delete procedure would be doing exactly what it was
built to do.

**(5,6) = 0.9769 — identifiers are invisible.** `pod-7f9b4c` and
`pod-7f9b4d` differ by one character and by everything that matters
operationally. The embedding cannot see the difference. Infrastructure
data is *full* of these: pod names, node IDs, error codes, ticket
numbers, image digests. This single number is the strongest argument in
the project so far for keyword search alongside vectors (Phase 4).

**All norms = 1.0000 — the model L2-normalises its output.** So for this
model cosine similarity equals the plain dot product, and Euclidean
distance is a monotonic function of cosine:

```
euclidean = sqrt(2 - 2 * cosine)
sqrt(2 - 2*0.9369) = 0.3552   (matches the measured value)
sqrt(2 - 2*0.0509) = 1.3777   (matches)
```

Which means: for *this* model, ranking by cosine and ranking by
Euclidean distance give the identical order. The choice only matters for
models that do not normalise — and when a vector database asks you to
pick an operator (`<=>` vs `<->` in pgvector), this is the question it
is really asking.

## Tradeoffs we accepted

- **CPU-only MiniLM.** ~90MB, milliseconds per batch, no API bill, no
  data leaving the machine. The cost is accuracy we have not measured
  yet. Upgrading is a one-line change in `embeddings.py` plus a full
  re-ingest — every stored vector must be regenerated, because old and
  new vectors are not comparable.
- **Brute-force search.** Exact, 20 lines, zero dependencies. Replaced
  in Phase 3 when the data outgrows a Python list.
- **Embed at ingestion, not at query time.** Query embedding is one call
  on the hot path; chunk embedding is a batch job done once.

## Lessons learned

1. Cosine similarity is four lines of Python. The library is convenience,
   not capability.
2. High similarity does not mean correct answer — (0,4) proves it.
3. Low similarity does not mean wrong answer — (0,3) proves it.
4. Embeddings are bad at exactly the thing infrastructure data is made
   of: unique identifiers. Plan for hybrid retrieval, not as an
   optimisation but as a correctness requirement.
5. A "similarity score" is only meaningful relative to other scores from
   the same model on the same corpus. Never hard-code a threshold you
   have not measured.
