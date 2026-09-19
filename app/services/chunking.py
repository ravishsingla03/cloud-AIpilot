"""
Chunking strategies.

Why this file exists:
    An embedding model turns a passage into one vector. One vector can
    only represent one idea well, so the size and the boundaries of the
    passage decide what retrieval can ever find:

      - too large: the vector is an average of five topics and matches
        every query weakly and none strongly, and the chunk drags four
        irrelevant paragraphs into the prompt with it.
      - too small: the chunk loses the context that made it meaningful
        ("Raise the limit" -- of what?).
      - wrong boundary: the answer is split across two chunks and
        neither one alone answers the question.

    Retrieval quality is decided here, before a single vector exists.
    This is the cheapest place in a RAG system to gain or lose accuracy.

A strategy is just a function: text -> [(section, content)].
    Passing a function around is all the polymorphism this needs. No
    base class, no registry -- ingestion.py takes whichever function you
    hand it.
"""

from __future__ import annotations

import re

# Markdown ATX headings: one to six '#' followed by a space and a title.
_HEADING = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)


def fixed_size(text: str, size: int = 120, overlap: int = 20) -> list[tuple[str | None, str]]:
    """
    Slide a fixed window over the text, ignoring its structure.

    The baseline every RAG tutorial starts with: cheap, uniform, and
    completely blind to what the document is saying. The overlap exists
    so that a sentence cut in half by a boundary still appears whole in
    the neighbouring chunk -- it buys back some of what the blind cut
    destroys, at the cost of storing the overlapping text twice.

    Words, not characters, so chunks never split mid-word. Real systems
    usually count tokens instead; words are close enough to reason about
    and need no tokenizer.
    """
    if overlap >= size:
        raise ValueError("overlap must be smaller than size, or the window never advances")

    words = text.split()
    step = size - overlap
    chunks: list[tuple[str | None, str]] = []
    for start in range(0, len(words), step):
        window = words[start : start + size]
        if not window:
            break
        # section is None: this strategy has no idea which section it is in.
        chunks.append((None, " ".join(window)))
        if start + size >= len(words):
            break  # the window already reached the end; a further slice
            # would only repeat text we have just emitted.
    return chunks


def heading_aware(text: str, max_words: int = 120, overlap: int = 20) -> list[tuple[str | None, str]]:
    """
    Split on markdown headings, so a chunk is one section of one document.

    The boundary the author already chose is almost always better than a
    boundary chosen by word count: a '## Cause: OOMKilled' section is one
    self-contained idea. The heading line is kept inside the chunk text
    because it names what the section is about, and that name is usually
    the strongest signal the embedding has.

    Sections longer than max_words fall back to fixed_size inside the
    section, so one rambling section cannot produce one giant vector.
    """
    chunks: list[tuple[str | None, str]] = []
    for heading, body in _split_sections(text):
        content = f"{heading}\n{body.strip()}" if heading else body.strip()
        if not content:
            continue
        if len(content.split()) <= max_words:
            chunks.append((heading, content))
        else:
            chunks.extend((heading, part) for _, part in fixed_size(content, max_words, overlap))
    return chunks


def _split_sections(text: str) -> list[tuple[str | None, str]]:
    """Cut the document at each heading; returns (heading_text, body)."""
    headings = list(_HEADING.finditer(text))
    if not headings:
        return [(None, text)]

    sections: list[tuple[str | None, str]] = []
    preamble = text[: headings[0].start()]
    if preamble.strip():
        sections.append((None, preamble))

    for match, following in zip(headings, headings[1:] + [None]):
        end = following.start() if following else len(text)
        sections.append((match.group(2).strip(), text[match.end() : end]))
    return sections
