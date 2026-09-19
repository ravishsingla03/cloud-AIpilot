"""
The ingestion pipeline: documents on disk -> chunks with metadata.

Why this file exists:
    Retrieval returns chunks, but a user needs an *answer with a
    citation*. "Raise the limit only after checking..." is useless on its
    own; "k8s-pod-crashloopbackoff.md > Cause: OOMKilled" is an answer
    they can verify. Metadata is not bookkeeping, it is what makes the
    output trustworthy, and it has to be attached at ingestion time
    because that is the only moment the surrounding context still exists.

The fields, and why each one is here:
    id           -- deterministic (document_id + index), so re-ingesting
                    the same document updates rows instead of duplicating
                    them when this moves to Postgres in Phase 3.
    document_id  -- groups chunks back into their source document.
    content      -- the text that gets embedded and put in the prompt.
    source       -- path for the citation; later a URL or a ticket id.
    title        -- document-level name, for display.
    section      -- which part of the document; empty for strategies that
                    do not know (that absence is itself a finding, see
                    docs/chunking.md).
    chunk_index  -- position in the document, so neighbouring chunks can
                    be fetched later ("expand the window" in Phase 4).
    metadata     -- open dict for anything strategy-specific; keeping it
                    open means a new experiment does not need a schema
                    change.
    created_at   -- when this chunk was produced. Infrastructure docs go
                    stale, and stale retrieved advice is worse than none.
"""

from __future__ import annotations

import re
from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from app.services.chunking import heading_aware

# A chunking strategy: text -> [(section, content)]
Chunker = Callable[[str], list[tuple[str | None, str]]]

_TITLE = re.compile(r"^#\s+(.+)$", re.MULTILINE)


@dataclass
class Chunk:
    id: str
    document_id: str
    content: str
    source: str
    title: str
    section: str
    chunk_index: int
    metadata: dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def citation(self) -> str:
        return f"{self.source} > {self.section}" if self.section else f"{self.source} #{self.chunk_index}"


def ingest_file(path: Path, chunker: Chunker = heading_aware, root: Path | None = None) -> list[Chunk]:
    """Reads one document and returns its chunks, in document order."""
    text = path.read_text(encoding="utf-8")
    document_id = path.relative_to(root).as_posix() if root else path.name
    title_match = _TITLE.search(text)
    title = title_match.group(1).strip() if title_match else path.stem

    return [
        Chunk(
            id=f"{document_id}#{index}",
            document_id=document_id,
            content=content,
            source=document_id,
            title=title,
            section=section or "",
            chunk_index=index,
            metadata={"strategy": getattr(chunker, "__name__", "custom"), "words": len(content.split())},
        )
        for index, (section, content) in enumerate(chunker(text))
    ]


def ingest_directory(
    root: Path, chunker: Chunker = heading_aware, pattern: str = "**/*.md"
) -> list[Chunk]:
    """Reads every matching document under root. Sorted so runs are reproducible."""
    return [
        chunk
        for path in sorted(root.glob(pattern))
        for chunk in ingest_file(path, chunker, root=root)
    ]
