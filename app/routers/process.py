"""Document processing endpoint — chains analyze, extract, summarize, validate."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.schemas import ToolResponse
from app.services.process import run_process_pipeline

router = APIRouter(tags=["tools"])


class ProcessRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Document text to process")
    document_type: str = Field(
        "auto",
        description="Document type hint: auto, invoice, contract, report, meeting_notes",
    )


@router.post("/process", response_model=ToolResponse)
def process(req: ProcessRequest) -> ToolResponse:
    """Run full document processing pipeline: analyze → extract → summarize → validate."""
    result = run_process_pipeline(req.text, document_type=req.document_type)
    return ToolResponse(success=True, data=result)
