"""Summarization tool — AI-powered with extractive fallback."""

from anthropic import Anthropic

SUMMARIZE_TOOL = {
    "name": "summarize",
    "description": (
        "Create a concise summary of the given text. "
        "Use this when you need to condense a long document into key takeaways. "
        "Supports different formats: 'bullets' for bullet points, 'paragraph' for prose."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "text": {
                "type": "string",
                "description": "The text to summarize",
            },
            "format": {
                "type": "string",
                "enum": ["bullets", "paragraph"],
                "description": "Output format: 'bullets' or 'paragraph'",
                "default": "bullets",
            },
            "max_points": {
                "type": "integer",
                "description": "Maximum number of bullet points (only for 'bullets' format)",
                "default": 5,
            },
        },
        "required": ["text"],
    },
}


def handle_summarize(
    text: str,
    format: str = "bullets",
    max_points: int = 5,
    api_key: str | None = None,
) -> dict:
    """Summarize text content.

    Uses Claude API when api_key is provided, otherwise falls back
    to extractive summarization (no API needed).

    Args:
        text: The text to summarize.
        format: Output format ('bullets' or 'paragraph').
        max_points: Max bullet points for 'bullets' format.
        api_key: Anthropic API key. If None, uses extractive fallback.

    Returns:
        Dictionary with summary, format, method used, and metadata.
    """
    sentences = _split_sentences(text)
    word_count = len(text.split())

    if api_key:
        summary = _ai_summarize(text, format, max_points, api_key)
        method = "ai"
    else:
        summary = _extractive_summarize(sentences, format, max_points)
        method = "extractive"

    return {
        "summary": summary,
        "format": format,
        "method": method,
        "original_word_count": word_count,
        "sentence_count": len(sentences),
    }


def _ai_summarize(text: str, format: str, max_points: int, api_key: str) -> str:
    """Use Claude to generate a genuine summary."""
    client = Anthropic(api_key=api_key)

    format_instruction = (
        f"Return exactly {max_points} bullet points, each starting with '- '"
        if format == "bullets"
        else "Return a single concise paragraph"
    )

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": (
                    f"Summarize the following text. {format_instruction}.\n"
                    f"Focus on the most important information.\n\n"
                    f"Text:\n{text}"
                ),
            }
        ],
    )
    block = response.content[0]
    if hasattr(block, "text"):
        return block.text  # type: ignore[union-attr]
    return str(block)


def _split_sentences(text: str) -> list[str]:
    """Split text into meaningful sentences, handling structured documents."""
    import re

    # First split by double newlines (paragraphs) — each is a potential sentence
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

    sentences = []
    for para in paragraphs:
        # Skip table-like content
        if "|" in para and para.count("|") > 2:
            continue
        # Skip very short lines (headers, labels)
        lines = [ln.strip() for ln in para.split("\n") if ln.strip()]
        for line in lines:
            # Split on sentence-ending punctuation, but not on abbreviations
            parts = re.split(r"(?<=[.!?])\s+(?=[A-Z])", line)
            for part in parts:
                cleaned = part.strip().rstrip(".")
                if cleaned and len(cleaned.split()) >= 2:
                    sentences.append(cleaned)

    return sentences


def _extractive_summarize(
    sentences: list[str], format: str, max_points: int
) -> str:
    """Extractive summarization — score sentences by importance signals."""
    if not sentences:
        return "No content to summarize."

    scored: list[tuple[float, int, str]] = []
    for i, s in enumerate(sentences):
        score = _score_sentence(s, i, len(sentences))
        scored.append((score, i, s))

    # Sort by score descending, then pick top N
    scored.sort(key=lambda x: x[0], reverse=True)
    top = scored[:max_points]

    # Re-sort by original position for coherent reading order
    top.sort(key=lambda x: x[1])

    if format == "bullets":
        return "\n".join(f"- {s.strip().lstrip('- ')}." for _, _, s in top)
    return ". ".join(s.strip().lstrip("- ") for _, _, s in top[:3]) + "."


def _score_sentence(sentence: str, position: int, total: int) -> float:
    """Score a sentence's importance using multiple heuristic signals."""
    score = 0.0
    lower = sentence.lower()
    words = sentence.split()
    word_count = len(words)

    # Length bonus — medium-length sentences are more informative
    if 8 <= word_count <= 30:
        score += 1.0
    elif word_count < 4:
        score -= 2.0  # Skip very short fragments

    # Position bonus — first sentences of document carry more weight
    if position == 0:
        score += 2.0
    elif position < total * 0.2:
        score += 1.0

    # Keyword signals — sentences with key terms are important
    importance_keywords = [
        "total", "key", "important", "result", "conclusion", "summary",
        "decision", "approved", "agreed", "deadline", "action", "revenue",
        "cost", "budget", "objective", "scope", "deliverable", "milestone",
    ]
    score += sum(0.5 for kw in importance_keywords if kw in lower)

    # Numeric data — sentences with numbers often carry facts
    import re
    numbers = re.findall(r"\d+[.,]?\d*", sentence)
    if numbers:
        score += 0.5 * min(len(numbers), 3)

    # Penalize boilerplate
    boilerplate = ["please", "regards", "sincerely", "dear", "hi ", "hello"]
    if any(bp in lower for bp in boilerplate):
        score -= 2.0

    # Penalize table-like fragments (pipe characters, dashes-only)
    if "|" in sentence or sentence.strip("-= ") == "":
        score -= 3.0

    return score
