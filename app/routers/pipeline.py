"""Pipeline endpoint — runs TypeScript automation pipelines."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from agent.tools.pipeline import handle_run_pipeline
from app.schemas import ToolResponse

router = APIRouter(tags=["tools"])


class PipelineRequest(BaseModel):
    task: str = Field(..., min_length=1, description="Description of the pipeline task")
    pipeline: str = Field("posts", description="Pipeline to run: posts or github")


@router.post("/pipeline", response_model=ToolResponse)
def pipeline(req: PipelineRequest) -> ToolResponse:
    """Run a data pipeline (posts or github) and return results."""
    result = handle_run_pipeline(task=req.task, pipeline=req.pipeline)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return ToolResponse(success=True, data=result)
