"""
A toy in-memory vector store.

Why this file exists:
    Before reaching for pgvector (Phase 3), we implement the thing a
    vector database actually does, so that "vector search" stops being
    magic. Stripped of indexes, persistence and SQL, a vector database
    is this: a list of (item, vector) pairs and a loop that scores the
    query against every one of them.

    Everything a real vector database adds on top -- an ANN index, disk
    persistence, concurrent writers, metadata filtering -- is an
    optimisation or an operational feature layered over this loop. If
    you can write this loop, you can reason about what those layers buy
    you and what they cost you.

Why cosine similarity:
    The embedding model returns direction, not magnitude: two texts that
    mean the same thing point the same way. Cosine compares direction
    only. See docs/embeddings.md for the experiment behind that claim.
"""

from __future__ import annotations

import heapq
import math
from typing import Any


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """Dot product divided by the product of both magnitudes."""
    return sum(x * y for x, y in zip(a, b)) / (math.hypot(*a) * math.hypot(*b))


class InMemoryVectorStore:
    """
    Stores (item, vector) pairs and finds the top-K nearest by cosine.

    `item` is deliberately untyped: the store does not care whether it
    holds a Chunk, a string, or a dict. That keeps the retrieval concept
    separate from the ingestion concept.
    """

    def __init__(self) -> None:
        # Each entry is (item, vector, norm). The norm is precomputed
        # because it never changes, and recomputing it inside every
        # query would double the per-query work for no reason.
        self._entries: list[tuple[Any, list[float], float]] = []

    def __len__(self) -> int:
        return len(self._entries)

    def add(self, item: Any, vector: list[float]) -> None:
        norm = math.hypot(*vector)
        if norm == 0:
            raise ValueError("cannot store a zero vector: it has no direction")
        self._entries.append((item, vector, norm))

    def add_many(self, items: list[Any], vectors: list[list[float]]) -> None:
        for item, vector in zip(items, vectors, strict=True):
            self.add(item, vector)

    def search(self, query_vector: list[float], top_k: int = 5) -> list[tuple[float, Any]]:
        """
        Returns the top_k (score, item) pairs, highest score first.

        ponytail: brute force, O(n * d) per query. Fine for thousands of
        chunks on a laptop; an ANN index (HNSW/IVFFlat, i.e. pgvector in
        Phase 3) is what you reach for when n stops fitting that budget.
        """
        query_norm = math.hypot(*query_vector)
        if query_norm == 0:
            raise ValueError("cannot search with a zero vector")

        scored = (
            (sum(x * y for x, y in zip(query_vector, vector)) / (query_norm * norm), item)
            for item, vector, norm in self._entries
        )
        # key= on the score only: without it, ties would make Python try
        # to compare the items themselves, which usually raises.
        return heapq.nlargest(top_k, scored, key=lambda pair: pair[0])
