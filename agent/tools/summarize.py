"""Summarization tool — creates concise summaries of text content."""

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
    text: str, format: str = "bullets", max_points: int = 5
) -> dict:
    """Summarize text content.

    Args:
        text: The text to summarize.
        format: Output format ('bullets' or 'paragraph').
        max_points: Max bullet points for 'bullets' format.

    Returns:
        Dictionary with summary and metadata.
    """
    sentences = [s.strip() for s in text.replace("\n", " ").split(".") if s.strip()]
    word_count = len(text.split())

    if format == "bullets":
        points = sentences[:max_points]
        summary = "\n".join(f"- {point}." for point in points)
    else:
        summary = ". ".join(sentences[:3]) + "."

    return {
        "summary": summary,
        "format": format,
        "original_word_count": word_count,
        "sentence_count": len(sentences),
    }
