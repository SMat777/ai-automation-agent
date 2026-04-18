"""Document analysis endpoint."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field

from agent.tools.analyze import handle_analyze
from app.schemas import ToolResponse

router = APIRouter(tags=["tools"])


class AnalyzeRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Document text to analyze")
    focus: str = Field(
        "general",
        description="Focus area: general, financial, technical, organizational",
    )


@router.post("/analyze", response_model=ToolResponse)
def analyze(req: AnalyzeRequest) -> ToolResponse:
    """Analyze a document — detect type, extract entities, key points, stats."""
    result = handle_analyze(req.text, focus=req.focus)
    return ToolResponse(success=True, data=result)
