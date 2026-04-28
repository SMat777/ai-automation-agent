"""Text embedding via OpenAI API.

Uses text-embedding-3-small (cheapest, good quality for demo).
Falls back gracefully when no API key is configured.
"""

from __future__ import annotations

import os
from functools import lru_cache

_MODEL = "text-embedding-3-small"


@lru_cache(maxsize=1)
def _get_client():  # type: ignore[no-untyped-def]
    """Lazy-init OpenAI client (only imported when actually needed)."""
    from openai import OpenAI  # noqa: PLC0415

    api_key = os.getenv("OPENAI_API_KEY", "")
    if not api_key:
        raise RuntimeError(
            "OPENAI_API_KEY not set. Required for embedding documents."
        )
    return OpenAI(api_key=api_key)


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed a batch of texts and return their vector representations.

    Args:
        texts: List of strings to embed.

    Returns:
        List of embedding vectors (one per input text).
    """
    if not texts:
        return []

    client = _get_client()
    response = client.embeddings.create(model=_MODEL, input=texts)
    return [item.embedding for item in response.data]


def embed_single(text: str) -> list[float]:
    """Embed a single text string.

    Args:
        text: The string to embed.

    Returns:
        Embedding vector as list of floats.
    """
    return embed_texts([text])[0]
