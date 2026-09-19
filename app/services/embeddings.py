"""
The embedding service.

Why this file exists:
    Every part of the system that needs a vector -- ingestion, query
    time, later the evaluation harness -- must use the *same* model.
    Vectors from two different models live in different spaces, and
    comparing them produces numbers that look plausible and mean
    nothing. One module owning the model makes that mistake hard.

Why all-MiniLM-L6-v2:
    384 dimensions, ~90MB, runs on CPU in milliseconds, and it is a
    sentence-similarity model rather than a raw language model, so its
    vectors are trained for exactly the comparison we do. Bigger models
    (bge-large, e5-large, OpenAI text-embedding-3) score better on
    benchmarks and cost more per call or per watt. We start small on
    purpose: Phase 4 measures retrieval quality, and only a measurement
    justifies paying for a bigger model.
"""

from __future__ import annotations

from functools import lru_cache

from sentence_transformers import SentenceTransformer

MODEL_NAME = "all-MiniLM-L6-v2"
EMBEDDING_DIM = 384


@lru_cache(maxsize=1)
def _model() -> SentenceTransformer:
    """Loads the model once per process. Loading costs seconds; encoding costs milliseconds."""
    return SentenceTransformer(MODEL_NAME)


def embed(texts: list[str]) -> list[list[float]]:
    """
    Encodes a batch of texts into vectors.

    Batching matters: one call with 100 texts is far faster than 100
    calls with one text, because the model runs them through the network
    in parallel.
    """
    return [[float(x) for x in vector] for vector in _model().encode(texts)]


def embed_one(text: str) -> list[float]:
    return embed([text])[0]
