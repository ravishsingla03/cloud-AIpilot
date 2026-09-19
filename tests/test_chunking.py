"""Run with:  python tests/test_chunking.py"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.chunking import fixed_size, heading_aware

DOC = """# Title

Intro line.

## Alpha

Alpha body text.

## Beta

Beta body text.
"""


def test_fixed_size_overlaps_and_covers_every_word():
    words = [f"w{i}" for i in range(25)]
    chunks = fixed_size(" ".join(words), size=10, overlap=3)

    assert [c.split()[0] for _, c in chunks] == ["w0", "w7", "w14", "w21"]
    assert chunks[-1][1].endswith("w24")  # nothing dropped off the end
    assert all(section is None for section, _ in chunks)
    # The overlap is real: the tail of one chunk is the head of the next.
    assert chunks[0][1].split()[-3:] == chunks[1][1].split()[:3]


def test_fixed_size_rejects_a_window_that_never_advances():
    try:
        fixed_size("a b c", size=5, overlap=5)
    except ValueError:
        return
    raise AssertionError("expected ValueError when overlap >= size")


def test_heading_aware_keeps_one_section_per_chunk():
    chunks = heading_aware(DOC)

    assert [section for section, _ in chunks] == ["Title", "Alpha", "Beta"]
    # The heading stays inside the chunk text, not only in the metadata.
    assert chunks[1][1] == "Alpha\nAlpha body text."


def test_heading_aware_splits_a_section_that_is_too_long():
    long_doc = "## Alpha\n\n" + " ".join(f"w{i}" for i in range(50))
    chunks = heading_aware(long_doc, max_words=20, overlap=5)

    assert len(chunks) > 1
    assert all(section == "Alpha" for section, _ in chunks)


if __name__ == "__main__":
    test_fixed_size_overlaps_and_covers_every_word()
    test_fixed_size_rejects_a_window_that_never_advances()
    test_heading_aware_keeps_one_section_per_chunk()
    test_heading_aware_splits_a_section_that_is_too_long()
    print("ok")
