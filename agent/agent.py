"""Core agent with decision loop and tool calling."""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field
from collections.abc import Generator
from typing import Any, Callable, cast

from anthropic import APIError, APITimeoutError, Anthropic, RateLimitError
from anthropic.types import Message, MessageParam, ToolParam, ToolResultBlockParam

from agent.prompts.system import AGENT_SYSTEM_PROMPT
from agent.tools import TOOLS, TOOL_HANDLERS

logger = logging.getLogger(__name__)


@dataclass
class AgentStep:
    """A single step in the agent's reasoning loop."""

    iteration: int
    action: str  # "think", "tool_call", "final_answer"
    tool_name: str | None = None
    tool_input: dict[str, Any] | None = None
    tool_result: dict[str, Any] | None = None
    text: str | None = None
    duration_ms: int = 0


@dataclass
class AgentResult:
    """Complete result from an agent run, including metadata."""

    answer: str
    steps: list[AgentStep] = field(default_factory=list)
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_duration_ms: int = 0
    iterations: int = 0

    @property
    def tool_calls(self) -> list[AgentStep]:
        return [s for s in self.steps if s.action == "tool_call"]


class StreamResult:
    """Wrapper for streaming agent output.

    Iterate to get text chunks. After iteration completes,
    access .result for the full AgentResult with metadata.

    Usage:
        stream = agent.run_stream("Summarize this report")
        for chunk in stream:
            print(chunk, end="", flush=True)
        print(f"Tokens used: {stream.result.total_input_tokens}")
    """

    def __init__(self, generator: Generator[str, None, AgentResult]) -> None:
        self._generator = generator
        self.result: AgentResult | None = None

    def __iter__(self) -> Generator[str, None, None]:
        self.result = yield from self._generator


class Agent:
    """AI agent that reasons about tasks and calls tools to accomplish them.

    The agent uses Claude's tool calling capability to decide which tools
    to use and how to parameterize them. It runs a ReAct loop:
    think -> act -> observe, repeating until it has a final answer.

    Usage:
        agent = Agent(api_key="sk-...")
        result = agent.run("Analyze this document and extract key metrics")
        print(result.answer)
        print(f"Used {result.iterations} iterations, {len(result.tool_calls)} tool calls")
    """

    def __init__(
        self,
        api_key: str,
        model: str = "claude-sonnet-4-20250514",
        max_retries: int = 3,
    ) -> None:
        self.api_key = api_key
        self.client = Anthropic(api_key=api_key)
        self.model = model
        self.max_retries = max_retries
        self.tools = [cast(ToolParam, tool) for tool in TOOLS]
        self.tool_handlers = TOOL_HANDLERS

    def run(self, task: str, max_iterations: int = 10) -> AgentResult:
        """Run the agent on a task and return a structured result.

        Args:
            task: The user's task description.
            max_iterations: Safety limit for the agent loop.

        Returns:
            AgentResult with the answer, steps taken, and usage metadata.
        """
        start_time = time.monotonic()
        messages: list[MessageParam] = [{"role": "user", "content": task}]
        result = AgentResult(answer="")

        logger.info("Agent started | task: %s", task[:100])

        for iteration in range(1, max_iterations + 1):
            logger.info("--- Iteration %d/%d ---", iteration, max_iterations)
            result.iterations = iteration

            response = self._call_api(messages)

            # Track token usage
            result.total_input_tokens += response.usage.input_tokens
            result.total_output_tokens += response.usage.output_tokens

            # Log any thinking text from the response
            for block in response.content:
                if block.type == "text" and block.text.strip():
                    logger.info("Agent thinks: %s", block.text[:200])
                    result.steps.append(AgentStep(
                        iteration=iteration,
                        action="think",
                        text=block.text,
                    ))

            if response.stop_reason == "end_turn":
                answer = self._extract_text(response)
                result.answer = answer
                result.steps.append(AgentStep(
                    iteration=iteration,
                    action="final_answer",
                    text=answer,
                ))
                logger.info("Agent finished | iterations: %d", iteration)
                break

            if response.stop_reason == "tool_use":
                messages.append({"role": "assistant", "content": response.content})

                tool_results: list[ToolResultBlockParam] = []
                for block in response.content:
                    if block.type == "tool_use":
                        step_start = time.monotonic()
                        tool_input = cast(dict[str, Any], block.input)

                        logger.info(
                            "Tool call: %s(%s)",
                            block.name,
                            json.dumps(tool_input, default=str)[:200],
                        )

                        tool_output = self._execute_tool(block.name, tool_input)
                        duration_ms = int((time.monotonic() - step_start) * 1000)

                        result.steps.append(AgentStep(
                            iteration=iteration,
                            action="tool_call",
                            tool_name=block.name,
                            tool_input=tool_input,
                            tool_result=tool_output,
                            duration_ms=duration_ms,
                        ))

                        logger.info(
                            "Tool result: %s -> %s (%dms)",
                            block.name,
                            json.dumps(tool_output, default=str)[:200],
                            duration_ms,
                        )

                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": json.dumps(tool_output, default=str),
                        })

                messages.append({"role": "user", "content": tool_results})
            else:
                logger.warning("Unexpected stop_reason: %s", response.stop_reason)
                result.answer = self._extract_text(response)
                break
        else:
            result.answer = (
                f"Agent reached maximum iterations ({max_iterations}) "
                "without completing the task."
            )
            logger.warning("Max iterations reached: %d", max_iterations)

        result.total_duration_ms = int((time.monotonic() - start_time) * 1000)
        logger.info(
            "Agent done | tokens: %d in + %d out | duration: %dms",
            result.total_input_tokens,
            result.total_output_tokens,
            result.total_duration_ms,
        )
        return result

    def run_stream(
        self, task: str, max_iterations: int = 10
    ) -> StreamResult:
        """Run the agent on a task, yielding text chunks as they stream in.

        Same ReAct loop as run(), but uses the streaming API so text arrives
        incrementally. Tool calls still execute synchronously between stream
        segments.

        Usage:
            stream = agent.run_stream("Summarize this report")
            for chunk in stream:
                print(chunk, end="", flush=True)
            print(stream.result.answer)  # AgentResult available after iteration

        Args:
            task: The user's task description.
            max_iterations: Safety limit for the agent loop.

        Returns:
            StreamResult — iterate for text chunks, then access .result for metadata.
        """
        return StreamResult(self._stream_generator(task, max_iterations))

    def _stream_generator(
        self, task: str, max_iterations: int
    ) -> Generator[str, None, AgentResult]:
        """Internal generator for streaming. Use run_stream() instead."""
        start_time = time.monotonic()
        messages: list[MessageParam] = [{"role": "user", "content": task}]
        result = AgentResult(answer="")

        logger.info("Agent (stream) started | task: %s", task[:100])

        for iteration in range(1, max_iterations + 1):
            result.iterations = iteration

            with self.client.messages.stream(
                model=self.model,
                max_tokens=4096,
                system=AGENT_SYSTEM_PROMPT,
                tools=self.tools,
                messages=messages,
            ) as stream:
                for text in stream.text_stream:
                    yield text

            response = stream.get_final_message()

            result.total_input_tokens += response.usage.input_tokens
            result.total_output_tokens += response.usage.output_tokens

            for block in response.content:
                if block.type == "text" and block.text.strip():
                    result.steps.append(AgentStep(
                        iteration=iteration,
                        action="think",
                        text=block.text,
                    ))

            if response.stop_reason == "end_turn":
                answer = self._extract_text(response)
                result.answer = answer
                result.steps.append(AgentStep(
                    iteration=iteration,
                    action="final_answer",
                    text=answer,
                ))
                break

            if response.stop_reason == "tool_use":
                messages.append({"role": "assistant", "content": response.content})

                tool_results: list[ToolResultBlockParam] = []
                for block in response.content:
                    if block.type == "tool_use":
                        step_start = time.monotonic()
                        tool_input = cast(dict[str, Any], block.input)
                        tool_output = self._execute_tool(block.name, tool_input)
                        duration_ms = int((time.monotonic() - step_start) * 1000)

                        result.steps.append(AgentStep(
                            iteration=iteration,
                            action="tool_call",
                            tool_name=block.name,
                            tool_input=tool_input,
                            tool_result=tool_output,
                            duration_ms=duration_ms,
                        ))

                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": json.dumps(tool_output, default=str),
                        })

                messages.append({"role": "user", "content": tool_results})
            else:
                result.answer = self._extract_text(response)
                break
        else:
            result.answer = (
                f"Agent reached maximum iterations ({max_iterations}) "
                "without completing the task."
            )

        result.total_duration_ms = int((time.monotonic() - start_time) * 1000)
        return result

    def _call_api(self, messages: list[MessageParam]) -> Message:
        """Call the Claude API with retry logic for transient errors."""
        last_error: Exception | None = None

        for attempt in range(1, self.max_retries + 1):
            try:
                return self.client.messages.create(
                    model=self.model,
                    max_tokens=4096,
                    system=AGENT_SYSTEM_PROMPT,
                    tools=self.tools,
                    messages=messages,
                )
            except RateLimitError as e:
                last_error = e
                wait = min(2**attempt, 30)
                logger.warning("Rate limited (attempt %d/%d), waiting %ds", attempt, self.max_retries, wait)
                time.sleep(wait)
            except APITimeoutError as e:
                last_error = e
                logger.warning("API timeout (attempt %d/%d)", attempt, self.max_retries)
            except APIError as e:
                status = getattr(e, "status_code", None)
                if status and status >= 500:
                    last_error = e
                    wait = min(2**attempt, 30)
                    logger.warning("Server error %s (attempt %d/%d)", status, attempt, self.max_retries)
                    time.sleep(wait)
                else:
                    raise

        raise last_error  # type: ignore[misc]

    def _execute_tool(self, name: str, params: dict[str, Any]) -> dict[str, Any]:
        """Execute a tool by name with the given parameters."""
        handler = cast(
            Callable[..., dict[str, Any]] | None,
            self.tool_handlers.get(name),
        )
        if handler is None:
            return {"error": f"Unknown tool: {name}"}

        try:
            if name == "summarize":
                params["api_key"] = self.api_key
            return handler(**params)
        except Exception as e:
            logger.error("Tool '%s' failed: %s", name, e)
            return {"error": f"Tool '{name}' failed: {str(e)}"}

    def _extract_text(self, response: Message) -> str:
        """Extract text content from a Claude response."""
        text_blocks = [
            block.text for block in response.content if block.type == "text"
        ]
        return "\n".join(text_blocks)
