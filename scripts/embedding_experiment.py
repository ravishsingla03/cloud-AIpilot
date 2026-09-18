
"""
Phase 2, experiment 1: does semantic similarity actually show up as geometry?

Run:  python scripts/embedding_experiment.py
"""

import math

from sentence_transformers import SentenceTransformer

SENTENCES = [
    "How do I restart a Kubernetes pod?",        # 0
    "Kubernetes pod restart procedure",          # 1
    "How do I cook pasta?",                      # 2
    "terminate and reschedule the workload",     # 3  - same meaning as 0, almost no shared words
    "How do I permanently delete a Kubernetes pod?",  # 4  - many shared words, opposite intent
    "pod-7f9b4c is crashing",                    # 5
    "pod-7f9b4d is crashing",                    # 6  - different pod, one character apart
]


def dot(a: list[float], b: list[float]) -> float:
    """Sum of elementwise products."""
    return sum(x * y for x, y in zip(a, b))


def norm(a: list[float]) -> float:
    """Vector magnitude: sqrt of the sum of squares."""
    return math.hypot(*a)


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """dot(a, b) divided by the product of both magnitudes."""
    return dot(a, b) / (norm(a) * norm(b))


def euclidean_distance(a: list[float], b: list[float]) -> float:
    """sqrt of the summed squared differences."""
    return math.hypot(*(x - y for x, y in zip(a, b)))


def main() -> None:
    model = SentenceTransformer("all-MiniLM-L6-v2")
    vectors = [list(v) for v in model.encode(SENTENCES)]

    print(f"dimensions: {len(vectors[0])}")
    for i, v in enumerate(vectors):
        print(f"  ||v{i}|| = {norm(v):.4f}")

    pairs = [(0, 1), (0, 2), (0, 3), (0, 4), (5, 6)]
    for i, j in pairs:
        cos = cosine_similarity(vectors[i], vectors[j])
        euc = euclidean_distance(vectors[i], vectors[j])
        print(f"({i},{j})  cosine={cos:+.4f}   euclidean={euc:.4f}")


if __name__ == "__main__":
    main()