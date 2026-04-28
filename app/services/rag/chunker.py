"""Recursive character text splitter for RAG pipeline.

Splits text into overlapping chunks, preferring natural boundaries
(paragraphs > sentences > words) to preserve semantic coherence.
"""

from __future__ import annotations

from dataclasses import dataclass

# Separators in priority order: paragraph > sentence > word > char
_SEPARATORS = ["\n\n", "\n", ". ", " "]


@dataclass(frozen=True, slots=True)
class Chunk:
    """A text chunk with its position index."""

    text: str
    index: int


def chunk_text(
    text: str,
    chunk_size: int = 500,
    overlap: int = 50,
) -> list[Chunk]:
    """Split *text* into overlapping chunks of at most *chunk_size* characters.

    Uses recursive splitting: tries paragraph boundaries first, then sentences,
    then words, then raw character splits as a last resort.

    Args:
        text: The source text to split.
        chunk_size: Maximum characters per chunk.
        overlap: Characters of overlap between consecutive chunks.

    Returns:
        List of Chunk objects with text and sequential index.
    """
    stripped = text.strip()
    if not stripped:
        return []

    if len(stripped) <= chunk_size:
        return [Chunk(text=stripped, index=0)]

    raw_pieces = _recursive_split(stripped, chunk_size, _SEPARATORS)
    return _merge_with_overlap(raw_pieces, chunk_size, overlap)


def _recursive_split(
    text: str,
    chunk_size: int,
    separators: list[str],
) -> list[str]:
    """Recursively split text using the highest-priority separator that works."""
    if len(text) <= chunk_size:
        return [text]

    for sep in separators:
        parts = text.split(sep)
        if len(parts) > 1:
            # This separator actually splits the text
            result: list[str] = []
            current = ""
            for part in parts:
                candidate = f"{current}{sep}{part}" if current else part
                if len(candidate) <= chunk_size:
                    current = candidate
                else:
                    if current:
                        result.append(current)
                    # If single part exceeds chunk_size, recurse with next separator
                    if len(part) > chunk_size:
                        remaining_seps = separators[separators.index(sep) + 1 :]
                        result.extend(
                            _recursive_split(part, chunk_size, remaining_seps)
                        )
                    else:
                        current = part
                        continue
                    current = ""
            if current:
                result.append(current)
            return result

    # No separator works — hard split by character
    return [text[i : i + chunk_size] for i in range(0, len(text), chunk_size)]


def _merge_with_overlap(
    pieces: list[str],
    chunk_size: int,
    overlap: int,
) -> list[Chunk]:
    """Merge small pieces and add overlap between consecutive chunks."""
    if not pieces:
        return []

    chunks: list[Chunk] = []
    idx = 0

    for piece in pieces:
        trimmed = piece.strip()
        if not trimmed:
            continue

        if chunks and overlap > 0:
            prev_text = chunks[-1].text
            # Take overlap from end of previous chunk
            overlap_text = prev_text[-overlap:].lstrip()
            combined = f"{overlap_text} {trimmed}".strip()
            if len(combined) <= chunk_size:
                trimmed = combined
            # If combined exceeds chunk_size, just use the piece as-is

        chunks.append(Chunk(text=trimmed, index=idx))
        idx += 1

    return chunks
