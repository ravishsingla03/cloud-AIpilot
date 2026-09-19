"""
Run with:  python tests/test_vector_store.py     (or pytest, when installed)

Hand-built vectors, no model: these tests check the search maths, not the
embeddings. A test that downloads a 90MB model to assert 2 + 2 is a test
nobody runs.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.vector_store import InMemoryVectorStore, cosine_similarity


def test_cosine_is_direction_not_magnitude():
    assert cosine_similarity([1.0, 0.0], [10.0, 0.0]) == 1.0
    assert cosine_similarity([1.0, 0.0], [0.0, 1.0]) == 0.0
    assert cosine_similarity([1.0, 0.0], [-1.0, 0.0]) == -1.0


def test_search_ranks_by_similarity_and_respects_top_k():
    store = InMemoryVectorStore()
    store.add_many(
        ["east", "north", "west"],
        [[1.0, 0.0], [0.0, 1.0], [-1.0, 0.0]],
    )

    hits = store.search([0.9, 0.1], top_k=2)

    assert [item for _, item in hits] == ["east", "north"]
    assert hits[0][0] > hits[1][0]
    assert len(store) == 3


def test_zero_vector_is_rejected():
    store = InMemoryVectorStore()
    for bad in (lambda: store.add("x", [0.0, 0.0]), lambda: store.search([0.0, 0.0])):
        try:
            bad()
        except ValueError:
            continue
        raise AssertionError("expected ValueError for a zero vector")


if __name__ == "__main__":
    test_cosine_is_direction_not_magnitude()
    test_search_ranks_by_similarity_and_respects_top_k()
    test_zero_vector_is_rejected()
    print("ok")
