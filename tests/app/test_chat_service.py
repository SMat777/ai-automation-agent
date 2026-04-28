"""Tests for chat streaming payload structure."""

from __future__ import annotations

import asyncio
import json
from types import SimpleNamespace
from unittest.mock import patch

from app.services.chat import demo_chat_stream, stream_agent_response


def _collect_events(async_iterable):
    """Collect all events from an async iterable in a sync test."""

    async def _collect():
        return [event async for event in async_iterable]

    return asyncio.run(_collect())


class TestDemoChatStream:
    """Demo mode stream should emit structured JSON payloads."""

    def test_emits_structured_json_for_text_tool_and_done_events(self):
        async def _no_sleep(_seconds: float) -> None:
            return None

        with patch("app.services.chat.asyncio.sleep", new=_no_sleep):
            events = _collect_events(demo_chat_stream("Please process this invoice"))

        text_event = next(e for e in events if e["event"] == "text")
        text_payload = json.loads(text_event["data"])
        assert text_payload["type"] == "text"
        assert isinstance(text_payload["content"], str)

        tool_event = next(e for e in events if e["event"] == "tool_call")
        tool_payload = json.loads(tool_event["data"])
        assert tool_payload["type"] == "tool_call"
        assert tool_payload["tool_name"] == "analyze_document"

        done_event = next(e for e in events if e["event"] == "done")
        done_payload = json.loads(done_event["data"])
        assert done_payload["type"] == "done"
        assert done_payload["demo_mode"] is True
        assert "answer" in done_payload


class TestLiveChatStream:
    """Live stream path should use the same structured payload contract."""

    def test_emits_tool_name_in_structured_tool_call_event(self):
        fake_step = SimpleNamespace(
            action="tool_call",
            tool_name="classify_email",
            tool_input={"subject": "Status"},
            tool_result={"category": "order_status"},
            duration_ms=42,
        )
        fake_result = SimpleNamespace(
            steps=[fake_step],
            answer="Done",
            iterations=1,
            tool_calls=[{"tool": "classify_email"}],
            total_input_tokens=10,
            total_output_tokens=20,
            total_duration_ms=120,
        )

        class _FakeStream:
            result = fake_result

            def __iter__(self):
                yield "Hello "
                yield "world"

        class _FakeAgent:
            def __init__(self, api_key: str):
                self.api_key = api_key

            def run_stream(self, _message: str, max_iterations: int):  # noqa: ARG002
                return _FakeStream()

        with patch("agent.agent.Agent", _FakeAgent):
            events = _collect_events(stream_agent_response("hi", api_key="test-key"))

        text_event = next(e for e in events if e["event"] == "text")
        text_payload = json.loads(text_event["data"])
        assert text_payload["type"] == "text"
        assert text_payload["content"] == "Hello "

        tool_event = next(e for e in events if e["event"] == "tool_call")
        tool_payload = json.loads(tool_event["data"])
        assert tool_payload["type"] == "tool_call"
        assert tool_payload["tool_name"] == "classify_email"

        done_event = next(e for e in events if e["event"] == "done")
        done_payload = json.loads(done_event["data"])
        assert done_payload["type"] == "done"
        assert done_payload["answer"] == "Done"
