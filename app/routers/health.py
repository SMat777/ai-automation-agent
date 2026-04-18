"""Health check endpoint."""

from __future__ import annotations

import os

from fastapi import APIRouter

from agent.tools.pipeline import AVAILABLE_PIPELINES

router = APIRouter(tags=["meta"])


@router.get("/health")
def health() -> dict:
    """Health check — reports whether the Anthropic API key is configured."""
    api_key_set = bool(os.getenv("ANTHROPIC_API_KEY"))
    return {
        "status": "ok",
        "api_key_configured": api_key_set,
        "available_tools": ["analyze", "extract", "summarize", "process", "pipeline", "chat"],
        "available_pipelines": list(AVAILABLE_PIPELINES.keys()),
    }
