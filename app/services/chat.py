"""Chat streaming service.

Produces SSE-compatible event dicts (shape: {"event": ..., "data": ...}) that
the chat router forwards via sse_starlette. The live path calls the real agent;
the demo path returns pre-written responses so the UI still works without an
API key.
"""

from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncGenerator, AsyncIterator


# ── Live agent path ──────────────────────────────────────────────────────────


async def stream_agent_response(message: str, api_key: str) -> AsyncGenerator[dict, None]:
    """Run the live agent on the user message and stream events as SSE dicts.

    Text chunks arrive first (as they are produced by Claude), followed by
    tool_call events, followed by a final `done` event with run metadata.
    """
    from agent.agent import Agent

    try:
        agent = Agent(api_key=api_key)
        stream = agent.run_stream(message, max_iterations=5)

        loop = asyncio.get_event_loop()

        def iterate_stream() -> tuple[list[str], object]:
            chunks: list[str] = []
            for chunk in stream:
                chunks.append(chunk)
            return chunks, stream.result

        chunks, result = await loop.run_in_executor(None, iterate_stream)

        for chunk in chunks:
            yield {"event": "text", "data": chunk}

        if result is not None:
            for step in result.steps:
                if step.action == "tool_call":
                    yield {
                        "event": "tool_call",
                        "data": json.dumps({
                            "tool": step.tool_name,
                            "input": step.tool_input,
                            "result": step.tool_result,
                            "duration_ms": step.duration_ms,
                        }),
                    }

            yield {
                "event": "done",
                "data": json.dumps({
                    "answer": result.answer,
                    "iterations": result.iterations,
                    "tool_calls": len(result.tool_calls),
                    "input_tokens": result.total_input_tokens,
                    "output_tokens": result.total_output_tokens,
                    "duration_ms": result.total_duration_ms,
                }),
            }

    except Exception as e:
        yield {"event": "error", "data": str(e)}


# ── Demo path (no API key) ───────────────────────────────────────────────────


async def demo_chat_stream(message: str) -> AsyncIterator[dict]:
    """Simulate agent responses when no API key is configured.

    Picks a contextual demo answer based on keywords in the user message and
    streams it character-by-character so the UI feels identical to the live path.
    """
    response, tool_calls = _pick_demo_response(message)

    for char in response:
        yield {"event": "text", "data": char}
        if char in (".", "\n"):
            await asyncio.sleep(0.02)
        elif char == " ":
            await asyncio.sleep(0.008)
        else:
            await asyncio.sleep(0.004)

    for tc in tool_calls:
        yield {"event": "tool_call", "data": json.dumps(tc)}

    yield {
        "event": "done",
        "data": json.dumps({
            "answer": response,
            "iterations": 1,
            "tool_calls": len(tool_calls),
            "input_tokens": 0,
            "output_tokens": len(response.split()),
            "duration_ms": len(response) * 5,
            "demo_mode": True,
        }),
    }


def _pick_demo_response(message: str) -> tuple[str, list[dict]]:
    """Select a contextual demo response based on keyword matches."""
    lower = message.lower()

    if any(kw in lower for kw in ("invoice", "faktura", "billing")):
        response = (
            "I can process invoices end-to-end! Here's how the pipeline works:\n\n"
            "**Step 1: Analysis** — I detect the document type and extract entities "
            "(dates, organizations, emails)\n\n"
            "**Step 2: Extraction** — I pull structured fields: Invoice Date, Due Date, "
            "Total, VAT, From, To, Reference\n\n"
            "**Step 3: Validation** — I check data consistency: does the total match "
            "subtotal + VAT? Is the due date after the invoice date?\n\n"
            "**Step 4: ERP Output** — I generate a structured JSON payload ready for "
            "import into Infor M3, Business Central, or SAP.\n\n"
            "Try it out — switch to the **Process** tab and paste an invoice, or click "
            'the "⚡ Process an invoice" demo card above!'
        )
        tool_calls = [{
            "tool": "analyze_document",
            "input": {"text": "(demo)", "focus": "general"},
            "result": {"document_type": "invoice"},
            "duration_ms": 145,
        }]
        return response, tool_calls

    if any(kw in lower for kw in ("analyze", "document", "report")):
        response = (
            "I'd be happy to analyze that document. I'll use the analyze tool to detect its type, "
            "extract entities, and identify key points.\n\n"
            "The analyze tool examines:\n"
            "- **Document type** — invoice, contract, email, report, etc.\n"
            "- **Entities** — emails, dates, URLs, organizations\n"
            "- **Structure** — heading hierarchy and sections\n"
            "- **Key points** — most important paragraphs\n\n"
            "Paste a document in the **Process** or **Analyze** tab and I'll show you what I find."
        )
        return response, []

    if any(kw in lower for kw in ("help", "what can", "how", "hvad kan")):
        response = (
            "I'm an AI agent that can help you process documents. Here's what I can do:\n\n"
            "🔍 **Analyze** — Detect document types, extract entities and structure\n"
            "📋 **Extract** — Pull structured data from invoices, contracts, tables\n"
            "✏️ **Summarize** — Condense long text into key takeaways\n"
            "⚡ **Process** — Run the full pipeline: analyze → extract → summarize → validate\n"
            "🔄 **Pipeline** — Fetch and transform data from live APIs\n\n"
            "I use a ReAct reasoning loop — I think about what tool to use, execute it, "
            "observe the result, and decide what to do next. "
            "Try the **Process** tab with an invoice to see all tools working together!"
        )
        return response, []

    response = (
        "I can help with that! As an AI automation agent, I work best when you give me "
        "a document to process or a specific task.\n\n"
        "Try asking me to:\n"
        '- "Analyze this invoice" (paste text in the Process tab)\n'
        '- "What can you do?"\n'
        '- "Summarize this report"\n\n'
        "Or click one of the **demo cards** above to see me in action."
    )
    return response, []
