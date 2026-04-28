"""Chat endpoint — SSE streaming to the web UI with post-stream run logging."""

from __future__ import annotations

import json
import logging
import os
import time
from collections.abc import AsyncIterator

from fastapi import APIRouter
from pydantic import BaseModel, Field
from sse_starlette.sse import EventSourceResponse

from app.db import SessionLocal
from app.services.chat import demo_chat_stream, stream_agent_response
from app.services.runs import log_run

router = APIRouter(tags=["agent"])
logger = logging.getLogger(__name__)


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="User message for the agent")


@router.post("/chat")
async def chat(req: ChatRequest) -> EventSourceResponse:
    """Chat with the AI agent. Streams responses via SSE.

    Event types (from the service layer):
        text        incremental text chunk
        tool_call   agent called a tool
        done        agent finished (payload includes run metadata)
        error       something went wrong

    Unlike the other endpoints, chat cannot use ``track_run`` — the request
    handler returns the moment we hand the generator to EventSourceResponse,
    but the agent keeps streaming afterwards. So we wrap the generator and
    log a Run row from inside it, once the stream finishes.
    """
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if api_key:
        source = stream_agent_response(req.message, api_key=api_key)
    else:
        source = demo_chat_stream(req.message)

    return EventSourceResponse(_logged_chat_stream(req.message, source))


# ── Post-stream run logging ──────────────────────────────────────────────────


async def _logged_chat_stream(
    message: str,
    source: AsyncIterator[dict],
) -> AsyncIterator[dict]:
    """Forward each event from the source stream, then log a Run at the end.

    Captures timing, token counts, and the final answer from the `done`
    event so we can persist them after the stream closes.
    """
    start = time.perf_counter()
    final_answer: str | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None
    status = "success"
    error_message: str | None = None

    try:
        async for event in source:
            # Inspect (but pass through unchanged) the events we care about.
            if event.get("event") == "done":
                try:
                    meta = json.loads(event.get("data", "{}"))
                    final_answer = meta.get("answer")
                    input_tokens = meta.get("input_tokens")
                    output_tokens = meta.get("output_tokens")
                except (ValueError, TypeError):
                    pass
            elif event.get("event") == "error":
                status = "error"
                error_message = str(event.get("data", ""))[:2000]

            yield event

    except Exception as exc:
        status = "error"
        error_message = f"{type(exc).__name__}: {exc}"
        raise
    finally:
        duration_ms = int((time.perf_counter() - start) * 1000)
        _persist_chat_run(
            message=message,
            answer=final_answer,
            duration_ms=duration_ms,
            status=status,
            error_message=error_message,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        )


def _persist_chat_run(
    *,
    message: str,
    answer: str | None,
    duration_ms: int,
    status: str,
    error_message: str | None,
    input_tokens: int | None,
    output_tokens: int | None,
) -> None:
    """Open a fresh session (the request-scoped one is already closed) and log."""
    db = SessionLocal()
    try:
        log_run(
            db,
            tool_name="chat",
            input_payload={"message": message},
            output_payload=({"answer": answer} if answer is not None else None),
            duration_ms=duration_ms,
            status=status,
            error_message=error_message,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        )
    except Exception as exc:
        logger.warning("Failed to persist chat run: %s", exc, exc_info=True)
    finally:
        db.close()
