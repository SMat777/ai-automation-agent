"""FastAPI application entry point.

Exposes the AI agent tools as a REST API and serves the web frontend.
Routers live in app/routers/; business logic in app/services/.
"""

from __future__ import annotations

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.routers import (
    analyze,
    chat,
    extract,
    health,
    knowledge,
    pipeline,
    process,
    runs,
    scenarios,
    stats,
    summarize,
    upload,
    workflows,
)

load_dotenv()

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncGenerator[None, None]:
    """Application startup and shutdown events."""
    # Startup: seed preset workflows
    from app.db.database import SessionLocal
    from app.services.workflow.seed import seed_preset_workflows

    db = SessionLocal()
    try:
        count = seed_preset_workflows(db)
        if count:
            logger.info("Seeded %d preset workflow(s) on startup", count)
    finally:
        db.close()

    yield  # Application runs here

    # Shutdown (nothing to clean up yet)


app = FastAPI(
    title="AI Automation Agent",
    description="AI-powered document analysis, data extraction, and automation pipelines",
    version="0.5.0",
    lifespan=lifespan,
)

# CORS is wide open for the current phase; ADR 004 / Fase 2 will tighten this.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── API routes ───────────────────────────────────────────────────────────────

API_PREFIX = "/api"

app.include_router(health.router, prefix=API_PREFIX)
app.include_router(analyze.router, prefix=API_PREFIX)
app.include_router(extract.router, prefix=API_PREFIX)
app.include_router(summarize.router, prefix=API_PREFIX)
app.include_router(process.router, prefix=API_PREFIX)
app.include_router(pipeline.router, prefix=API_PREFIX)
app.include_router(chat.router, prefix=API_PREFIX)
app.include_router(runs.router, prefix=API_PREFIX)
app.include_router(upload.router)  # prefix built-in
app.include_router(knowledge.router)  # prefix built-in
app.include_router(scenarios.router)  # prefix built-in
app.include_router(stats.router)  # prefix built-in
app.include_router(workflows.router)  # prefix built-in


# ── Frontend ─────────────────────────────────────────────────────────────────

app.mount("/static", StaticFiles(directory="frontend"), name="static")


@app.get("/", include_in_schema=False)
def serve_frontend() -> FileResponse:
    """Serve the SPA shell."""
    return FileResponse("frontend/index.html")
