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
    sentences = [s.strip() for s in text.replace("\n", " ").split(".") if s.strip()]
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


def _extractive_summarize(
    sentences: list[str], format: str, max_points: int
) -> str:
    """Fallback: simple extractive summarization (no API needed)."""
    if format == "bullets":
        points = sentences[:max_points]
        return "\n".join(f"- {point}." for point in points)
    return ". ".join(sentences[:3]) + "."
