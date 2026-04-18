"""Summarization endpoint."""

from __future__ import annotations

import os

from fastapi import APIRouter
from pydantic import BaseModel, Field

from agent.tools.summarize import handle_summarize
from app.schemas import ToolResponse

router = APIRouter(tags=["tools"])


class SummarizeRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Text to summarize")
    format: str = Field("bullets", description="Output format: bullets or paragraph")
    max_points: int = Field(5, ge=1, le=20, description="Max bullet points")


@router.post("/summarize", response_model=ToolResponse)
def summarize(req: SummarizeRequest) -> ToolResponse:
    """Summarize text. Uses AI when an API key is configured, otherwise extractive."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    result = handle_summarize(
        req.text,
        format=req.format,
        max_points=req.max_points,
        api_key=api_key,
    )
    return ToolResponse(success=True, data=result)
