"""Document analysis tool — extracts structure and key points from text."""

ANALYZE_TOOL = {
    "name": "analyze_document",
    "description": (
        "Analyze a document to extract its structure, key points, and main topics. "
        "Use this when you need to understand what a document contains before "
        "extracting specific data from it."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "text": {
                "type": "string",
                "description": "The document text to analyze",
            },
            "focus": {
                "type": "string",
                "description": "Optional focus area (e.g., 'financial', 'technical', 'organizational')",
                "default": "general",
            },
        },
        "required": ["text"],
    },
}


def handle_analyze(text: str, focus: str = "general") -> dict:
    """Analyze document structure and extract key points.

    Args:
        text: The document text to analyze.
        focus: Optional focus area for the analysis.

    Returns:
        Dictionary with sections, key_points, and word_count.
    """
    lines = text.strip().split("\n")
    sections = [line.strip() for line in lines if line.strip().startswith("#")]
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

    return {
        "sections": sections,
        "paragraph_count": len(paragraphs),
        "word_count": len(text.split()),
        "focus": focus,
        "key_points": [p[:100] + "..." if len(p) > 100 else p for p in paragraphs[:5]],
    }
