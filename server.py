"""FastAPI server — exposes AI agent tools as a REST API with web frontend."""

from __future__ import annotations

import os
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from agent.tools.analyze import handle_analyze
from agent.tools.extract import handle_extract
from agent.tools.summarize import handle_summarize
from agent.tools.pipeline import handle_run_pipeline, AVAILABLE_PIPELINES

load_dotenv()

app = FastAPI(
    title="AI Automation Agent",
    description="AI-powered document analysis, data extraction, and automation pipelines",
    version="0.4.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request/Response models ──────────────────────────────────────────────────


class AnalyzeRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Document text to analyze")
    focus: str = Field("general", description="Focus area: general, financial, technical, organizational")


class ExtractRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Text to extract data from")
    fields: list[str] = Field(..., min_length=1, description="Field names to extract")
    strategy: str = Field("auto", description="Strategy: auto, key_value, table, list")


class SummarizeRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Text to summarize")
    format: str = Field("bullets", description="Output format: bullets or paragraph")
    max_points: int = Field(5, ge=1, le=20, description="Max bullet points")


class PipelineRequest(BaseModel):
    task: str = Field(..., min_length=1, description="Description of the pipeline task")
    pipeline: str = Field("posts", description="Pipeline to run: posts or github")


class ToolResponse(BaseModel):
    success: bool
    data: dict[str, Any]


# ── API endpoints ────────────────────────────────────────────────────────────


@app.get("/api/health")
def health() -> dict:
    """Health check endpoint."""
    api_key_set = bool(os.getenv("ANTHROPIC_API_KEY"))
    return {
        "status": "ok",
        "api_key_configured": api_key_set,
        "available_tools": ["analyze", "extract", "summarize", "pipeline"],
        "available_pipelines": list(AVAILABLE_PIPELINES.keys()),
    }


@app.post("/api/analyze", response_model=ToolResponse)
def analyze(req: AnalyzeRequest) -> ToolResponse:
    """Analyze a document — detect type, extract entities, key points, stats."""
    result = handle_analyze(req.text, focus=req.focus)
    return ToolResponse(success=True, data=result)


@app.post("/api/extract", response_model=ToolResponse)
def extract(req: ExtractRequest) -> ToolResponse:
    """Extract structured data from text using key-value, table, or list strategies."""
    result = handle_extract(req.text, fields=req.fields, strategy=req.strategy)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return ToolResponse(success=True, data=result)


@app.post("/api/summarize", response_model=ToolResponse)
def summarize(req: SummarizeRequest) -> ToolResponse:
    """Summarize text. Uses AI when API key is configured, otherwise extractive."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    result = handle_summarize(
        req.text,
        format=req.format,
        max_points=req.max_points,
        api_key=api_key,
    )
    return ToolResponse(success=True, data=result)


@app.post("/api/pipeline", response_model=ToolResponse)
def pipeline(req: PipelineRequest) -> ToolResponse:
    """Run a data pipeline (posts or github) and return results."""
    result = handle_run_pipeline(task=req.task, pipeline=req.pipeline)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return ToolResponse(success=True, data=result)


# ── Frontend ─────────────────────────────────────────────────────────────────


app.mount("/static", StaticFiles(directory="frontend"), name="static")


@app.get("/")
def serve_frontend() -> FileResponse:
    """Serve the web frontend."""
    return FileResponse("frontend/index.html")
