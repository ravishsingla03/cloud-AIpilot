# Chunking

> Phase 2. Code: `app/services/chunking.py`, `app/services/ingestion.py`,
> `scripts/chunking_comparison.py`. Corpus: `data/docs/`.

## The problem

An embedding model turns a passage into exactly one vector, however long
the passage is. So a whole document becomes one point in space — the
average of everything it says. Ask "monitor clock skew" and a 1200-word
Ceph runbook that covers PGs, OSDs, nearfull and clock skew matches
weakly on all four and strongly on none.

Splitting is therefore not a preprocessing detail. The chunk is the unit
of retrieval, the unit of citation, and the unit the LLM eventually
reads. Where the cuts fall decides what the system can *ever* find.

## The concept

Two failure modes pull in opposite directions:

- **Chunks too large** — the vector is an average of several topics
  (dilution), and every retrieved chunk drags irrelevant paragraphs into
  a limited prompt budget.
- **Chunks too small** — the chunk loses the context that made it
  meaningful. "Raise the limit only after checking..." — the limit of
  what?

Between those, the interesting variable is *where* you cut, not just how
big the pieces are. Two strategies, both implemented here:

1. **Fixed-size** (`fixed_size`): slide a window of N words with an
   overlap of M. Structure-blind, works on any text. The overlap exists
   so a sentence severed by one boundary survives whole in its
   neighbour — it buys back part of what the blind cut destroyed, at the
   cost of storing overlapping text twice.
2. **Heading-aware** (`heading_aware`): cut on markdown headings, keep
   the heading line inside the chunk, and fall back to `fixed_size`
   inside any section that is still too long. The author already decided
   where one idea ends; use their decision.

A strategy here is just a function `text -> [(section, content)]`.
`ingestion.py` takes whichever function you hand it. No base class, no
registry — one-implementation interfaces are how a codebase gets heavy.

## The alternatives we did not build

| Strategy | Idea | Why not now |
|---|---|---|
| Recursive character splitting | Split on paragraph breaks, then lines, then spaces, until pieces fit | Basically heading-aware with a fallback ladder; more code, no measurable win on markdown yet |
| Sentence-window | Embed one sentence, return it with its neighbours | Needs a sentence splitter and a second store; worth revisiting once retrieval is measured |
| Semantic chunking | Embed sentences, cut where consecutive similarity drops | N embedding calls per document at ingest, plus a threshold to tune. Expensive guesswork before we can measure. |
| Parent-document retrieval | Search small chunks, return the big parent | Needs the parent/child link in the store — natural in Phase 3 where rows already have a `document_id` |
| LLM-based chunking | Ask a model where to cut | A per-document LLM bill for a problem a regex solves on structured docs |

## The implementation

Metadata is attached at ingestion time because that is the only moment
the surrounding context still exists. Once a chunk is a vector, nothing
can recover which document or section it came from. `Chunk` carries
`id, document_id, content, source, title, section, chunk_index,
metadata, created_at`, and `citation()` renders
`k8s-pod-pending.md > Cause: taints without matching tolerations`.

The `id` is deterministic (`document_id#chunk_index`) so that
re-ingesting a document in Phase 3 updates rows instead of duplicating
them.

## The experiment

`python scripts/chunking_comparison.py` — same four documents (1260
words of Kubernetes/Ceph/MinIO notes), same model, same queries; only
the boundaries differ.

```
    fixed_size:  13 chunks  words min/avg/max = 61/110/120
 heading_aware:  21 chunks  words min/avg/max = 46/57/75
```

### Case 1 — dilution. "monitor clock skew"

```
[fixed_size]
  +0.4169  ceph-health-warn.md #2
           ## OSD nearfull and backfillfull  Ceph raises nearfull at 85 percent ...
[heading_aware]
  +0.6653  ceph-health-warn.md > Clock skew and monitor quorum
           Clock skew and monitor quorum  Monitors report clock skew when their times drift ...
```

Both chunks contain the answer — fixed chunk #2 runs from "OSD nearfull"
all the way through "fix NTP on the monitor hosts". But that chunk's
single vector is the average of two unrelated topics, and the answer is
the minority of it: **0.4169 vs 0.6653**, a 0.25 gap on identical
underlying text. Worse, the citation it produces says *nearfull*, which
is not what the user asked about. Same corpus, same model, same query —
the boundary alone caused it.

### Case 2 — the section label is the answer

Query: "pod will not schedule because the node has a taint"

```
[fixed_size]     +0.7008  k8s-pod-pending.md #2
[heading_aware]  +0.7758  k8s-pod-pending.md > Cause: taints without matching tolerations
```

Both retrieve the right text. Only one can say *which cause* it is. When
this becomes a cited answer in Phase 3, that difference is the whole
user-visible product.

### Case 3 — a bigger chunk can score higher and answer less

Query: "how many drives can I lose before MinIO stops serving reads"

```
[fixed_size]     +0.6456  minio-drive-offline.md #0   (title + Symptom section)
                 +0.4344  minio-drive-offline.md #1   <- holds the actual quorum numbers
[heading_aware]  +0.6333  minio-drive-offline.md > Symptom
                 +0.5744  minio-drive-offline.md > How much loss the deployment tolerates
```

The highest-scoring chunk in the run (0.6456) does not contain the
answer; it just has more words that resemble the question. A longer
chunk offers more surface for a query to match, so raw score is not
evidence of correctness — it is evidence of overlap.

### Case 4 — both strategies got it wrong

Query: "why does my pod keep getting killed for using too much memory"

The correct section is `Cause: OOMKilled`. Fixed-size put it at rank 3
(0.5347); heading-aware put it at rank 3 (0.5226), behind `Symptom`
(0.5701) and a chunk from a *different document* about insufficient
memory at scheduling time (0.5285).

Nothing about chunking fixes this. The query says "killed for using too
much memory", the section says "exit code 137 and reason OOMKilled" —
the same vocabulary blind spot measured in `docs/embeddings.md` (the
0.1677 case). Phase 4 is where ranking quality gets measured and
attacked properly.

### Case 5 — a defect the comparison exposed

The first run produced 25 heading-aware chunks with a minimum size of
**4 words**: every document's H1 sits directly above its first H2, so
each one produced a chunk of pure title. Those chunks took **rank 3 on
two of the four queries at ~0.52**, pushing real content out of the
results while answering nothing.

The fix is one guard in `heading_aware` (skip sections with an empty
body). After it: 21 chunks, minimum 46 words, and on the OOMKilled query
the title-only chunk at rank 3 was replaced by the genuine
`Cause: OOMKilled` section at 0.5226. Measured, changed one thing,
measured again — and it only surfaced because the experiment printed
chunk sizes next to the hits.

## Tradeoffs we accepted

- **Words, not tokens.** Real systems count tokens, because tokens are
  what the LLM charges for. Words need no tokenizer and stay within
  roughly 30% of tokens for English prose. Revisit when prompt size
  starts costing money.
- **120 words / 20 overlap.** Not tuned — a starting point. Tuning
  without a labelled query set is guessing (Phase 4).
- **Heading-aware only understands markdown.** Kubernetes events, YAML
  manifests and log streams have no headings; Phase 5 telemetry will
  need a different splitter. Fixed-size stays as the fallback precisely
  because it assumes nothing.
- **Overlap duplicates text.** The 13 fixed-size chunks hold ~1430 words
  of a 1260-word corpus. Storage is cheap; the same passage appearing
  twice in one result set is not — dedup becomes real in Phase 4.

## Lessons learned

1. Chunking sets the ceiling on retrieval quality. No amount of clever
   ranking recovers an answer that was split in half at ingestion.
2. Structure the author already wrote (headings) beats a boundary chosen
   by word count — when the structure exists.
3. The section label is not decoration; it is what makes an answer
   citable and checkable.
4. A higher similarity score does not mean a better chunk. Length
   inflates scores.
5. Four hand-picked queries are anecdotes, not a metric. Everything here
   is directional evidence, not Recall@K — that needs a labelled set,
   which is Phase 4's job. These numbers do not belong on a résumé.
