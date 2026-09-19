"""
Phase 2, experiment 2: does the chunking strategy change what we retrieve?

Same corpus, same embedding model, same queries -- only the boundaries
differ. Run:  python scripts/chunking_comparison.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.chunking import fixed_size, heading_aware
from app.services.embeddings import embed, embed_one
from app.services.ingestion import Chunk, ingest_directory
from app.services.vector_store import InMemoryVectorStore

CORPUS = Path(__file__).resolve().parents[1] / "data" / "docs"

QUERIES = [
    "why does my pod keep getting killed for using too much memory",
    "pod will not schedule because the node has a taint",
    "how many drives can I lose before MinIO stops serving reads",
    "monitor clock skew",
]


def build_store(chunker) -> tuple[InMemoryVectorStore, list[Chunk]]:
    chunks = ingest_directory(CORPUS, chunker)
    store = InMemoryVectorStore()
    store.add_many(chunks, embed([c.content for c in chunks]))
    return store, chunks


def main() -> None:
    stores = {}
    for chunker in (fixed_size, heading_aware):
        store, chunks = build_store(chunker)
        stores[chunker.__name__] = store
        words = [c.metadata["words"] for c in chunks]
        print(
            f"{chunker.__name__:>14}: {len(chunks):3d} chunks  "
            f"words min/avg/max = {min(words)}/{sum(words) // len(words)}/{max(words)}"
        )

    for query in QUERIES:
        print(f"\nQ: {query}")
        query_vector = embed_one(query)
        for name, store in stores.items():
            print(f"  [{name}]")
            for score, chunk in store.search(query_vector, top_k=3):
                snippet = " ".join(chunk.content.split())[:110]
                print(f"    {score:+.4f}  {chunk.citation()}")
                print(f"            {snippet}...")


if __name__ == "__main__":
    main()
