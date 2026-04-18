"""Chat endpoint — SSE streaming to the web UI."""

from __future__ import annotations

import os

from fastapi import APIRouter
from pydantic import BaseModel, Field
from sse_starlette.sse import EventSourceResponse

from app.services.chat import demo_chat_stream, stream_agent_response

router = APIRouter(tags=["agent"])


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
    """
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return EventSourceResponse(demo_chat_stream(req.message))
    return EventSourceResponse(stream_agent_response(req.message, api_key=api_key))
