"""Document analysis endpoint."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from agent.tools.analyze import handle_analyze
from app.db import get_db
from app.schemas import ToolResponse
from app.services.run_tracker import track_run

router = APIRouter(tags=["tools"])


class AnalyzeRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Document text to analyze")
    focus: str = Field(
        "general",
        description="Focus area: general, financial, technical, organizational",
    )


@router.post("/analyze", response_model=ToolResponse)
def analyze(
    req: AnalyzeRequest,
    db: Session = Depends(get_db),
) -> ToolResponse:
    """Analyze a document — detect type, extract entities, key points, stats."""
    with track_run(db, tool_name="analyze", input_payload=req.model_dump()) as tr:
        result = handle_analyze(req.text, focus=req.focus)
        tr.output = result
    return ToolResponse(success=True, data=result)
