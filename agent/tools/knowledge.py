"""Knowledge base search tool — queries the RAG pipeline for relevant context.

Allows the agent to answer questions using previously uploaded documents.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Any

KNOWLEDGE_TOOL = {
    "name": "search_knowledge",
    "description": (
        "Search the knowledge base for information from uploaded documents. "
        "Use this when the user asks questions that might be answered by "
        "documents in the system — contracts, invoices, emails, reports, etc. "
        "Returns relevant text passages with source citations."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The search query in natural language",
            },
            "n_results": {
                "type": "integer",
                "description": "Number of results to return (default 5)",
                "default": 5,
            },
        },
        "required": ["query"],
    },
}


@lru_cache(maxsize=1)
def _get_retriever():  # type: ignore[no-untyped-def]
    """Lazy-init retriever (avoids import cost until actually needed)."""
    from app.services.rag.retriever import Retriever  # noqa: PLC0415

    return Retriever()


def handle_search_knowledge(
    query: str | None = None,
    n_results: int = 5,
    **kwargs: Any,
) -> dict[str, Any]:
    """Execute a knowledge base search and return formatted results.

    Supports both direct keyword arguments (agent dispatch path) and the
    legacy dict-based call style used in older tests/helpers.
    """
    # Backward compatibility: allow handle_search_knowledge({"query": ...})
    if isinstance(query, dict):
        params = query
        query = params.get("query")
        n_results = params.get("n_results", n_results)

    # Extra fallback for callers that pass a "params" kwarg explicitly
    if not query and isinstance(kwargs.get("params"), dict):
        params = kwargs["params"]
        query = params.get("query")
        n_results = params.get("n_results", n_results)

    if not query:
        return {"error": "Missing required parameter: query"}

    try:
        retriever = _get_retriever()
        results = retriever.search(query, n_results=n_results)

        if not results:
            return {
                "status": "not_found",
                "context": "No relevant documents found in knowledge base.",
                "sources": [],
            }

        context = retriever.format_context(results)
        sources = [
            {
                "source": r.source,
                "doc_id": r.doc_id,
                "score": r.score,
                "preview": r.text[:150],
            }
            for r in results
        ]

        return {
            "status": "found",
            "context": context,
            "sources": sources,
            "result_count": len(results),
        }

    except RuntimeError as exc:
        # Likely missing API key for embeddings
        return {"error": str(exc)}
