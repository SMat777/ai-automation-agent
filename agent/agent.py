"""Core agent with decision loop and tool calling."""

from __future__ import annotations

import json
from typing import Any, Callable, cast

from anthropic import Anthropic
from anthropic.types import Message, MessageParam, ToolParam, ToolResultBlockParam

from agent.prompts.system import AGENT_SYSTEM_PROMPT
from agent.tools import TOOLS, TOOL_HANDLERS


class Agent:
    """AI agent that reasons about tasks and calls tools to accomplish them.

    The agent uses Claude's tool calling capability to decide which tools
    to use and how to parameterize them. It runs a loop: think -> act -> observe
    until it has enough information to return a final answer.
    """

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514") -> None:
        self.client = Anthropic(api_key=api_key)
        self.model = model
        self.tools = [cast(ToolParam, tool) for tool in TOOLS]
        self.tool_handlers = TOOL_HANDLERS

    def run(self, task: str, max_iterations: int = 10) -> str:
        """Run the agent on a task and return the final answer.

        Args:
            task: The user's task description.
            max_iterations: Safety limit for the agent loop.

        Returns:
            The agent's final text response.
        """
        messages: list[MessageParam] = [{"role": "user", "content": task}]

        for _ in range(max_iterations):
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                system=AGENT_SYSTEM_PROMPT,
                tools=self.tools,
                messages=messages,
            )

            # Check if the agent wants to use tools or return a final answer
            if response.stop_reason == "end_turn":
                return self._extract_text(response)

            if response.stop_reason == "tool_use":
                # Add assistant response to conversation
                messages.append({"role": "assistant", "content": response.content})

                # Execute each tool call and collect results
                tool_results: list[ToolResultBlockParam] = []
                for block in response.content:
                    if block.type == "tool_use":
                        result = self._execute_tool(
                            block.name, cast(dict[str, Any], block.input)
                        )
                        tool_results.append(
                            {
                                "type": "tool_result",
                                "tool_use_id": block.id,
                                "content": json.dumps(result),
                            }
                        )

                messages.append({"role": "user", "content": tool_results})
            else:
                # Unexpected stop reason — return what we have
                return self._extract_text(response)

        return "Agent reached maximum iterations without completing the task."

    def _execute_tool(self, name: str, params: dict[str, Any]) -> dict[str, Any]:
        """Execute a tool by name with the given parameters.

        Args:
            name: The tool name to execute.
            params: Parameters to pass to the tool handler.

        Returns:
            Tool execution result as a dictionary.
        """
        handler = cast(Callable[..., dict[str, Any]] | None, self.tool_handlers.get(name))
        if handler is None:
            return {"error": f"Unknown tool: {name}"}

        try:
            return handler(**params)
        except Exception as e:
            return {"error": f"Tool '{name}' failed: {str(e)}"}

    def _extract_text(self, response: Message) -> str:
        """Extract text content from a Claude response."""
        text_blocks = [
            block.text for block in response.content if block.type == "text"
        ]
        return "\n".join(text_blocks)
