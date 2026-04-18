"""Data extraction endpoint."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from agent.tools.extract import handle_extract
from app.schemas import ToolResponse

router = APIRouter(tags=["tools"])


class ExtractRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Text to extract data from")
    fields: list[str] = Field(..., min_length=1, description="Field names to extract")
    strategy: str = Field("auto", description="Strategy: auto, key_value, table, list")


@router.post("/extract", response_model=ToolResponse)
def extract(req: ExtractRequest) -> ToolResponse:
    """Extract structured data from text using key-value, table, or list strategies."""
    result = handle_extract(req.text, fields=req.fields, strategy=req.strategy)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return ToolResponse(success=True, data=result)
