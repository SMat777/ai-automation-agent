"""Tests for Agent.run() — verifies the ReAct loop with mocked API calls."""

from unittest.mock import MagicMock, patch

from anthropic import RateLimitError
from anthropic.types import Message, TextBlock, ToolUseBlock, Usage

from agent.agent import Agent


def _make_message(
    content: list,
    stop_reason: str = "end_turn",
    input_tokens: int = 10,
    output_tokens: int = 5,
) -> Message:
    """Helper to build a mock Message with minimal boilerplate."""
    return Message(
        id="msg_test",
        type="message",
        role="assistant",
        content=content,
        model="claude-sonnet-4-20250514",
        stop_reason=stop_reason,
        usage=Usage(input_tokens=input_tokens, output_tokens=output_tokens),
    )


class TestAgentDirectAnswer:
    """Agent answers without calling any tools."""

    @patch("agent.agent.Anthropic")
    def test_returns_text_answer(self, mock_anthropic_cls: MagicMock) -> None:
        mock_client = MagicMock()
        mock_anthropic_cls.return_value = mock_client
        mock_client.messages.create.return_value = _make_message(
            content=[TextBlock(type="text", text="The answer is 42.")],
        )

        agent = Agent(api_key="test-key")
        result = agent.run("What is the meaning of life?")

        assert result.answer == "The answer is 42."
        assert result.iterations == 1
        assert len(result.tool_calls) == 0
        assert result.total_input_tokens == 10
        assert result.total_output_tokens == 5

    @patch("agent.agent.Anthropic")
    def test_records_thinking_step(self, mock_anthropic_cls: MagicMock) -> None:
        mock_client = MagicMock()
        mock_anthropic_cls.return_value = mock_client
        mock_client.messages.create.return_value = _make_message(
            content=[TextBlock(type="text", text="Here is my analysis.")],
        )

        agent = Agent(api_key="test-key")
        result = agent.run("Analyze this")

        think_steps = [s for s in result.steps if s.action == "think"]
        assert len(think_steps) == 1
        assert think_steps[0].text == "Here is my analysis."


class TestAgentToolCall:
    """Agent calls a tool, observes result, then answers."""

    @patch("agent.agent.Anthropic")
    def test_single_tool_call_then_answer(self, mock_anthropic_cls: MagicMock) -> None:
        mock_client = MagicMock()
        mock_anthropic_cls.return_value = mock_client

        # First response: agent wants to call analyze_document
        tool_response = _make_message(
            content=[
                TextBlock(type="text", text="Let me analyze this."),
                ToolUseBlock(
                    type="tool_use",
                    id="toolu_1",
                    name="analyze_document",
                    input={"text": "Hello world"},
                ),
            ],
            stop_reason="tool_use",
            input_tokens=20,
            output_tokens=15,
        )
        # Second response: agent gives final answer
        final_response = _make_message(
            content=[TextBlock(type="text", text="The document is general text.")],
            input_tokens=30,
            output_tokens=10,
        )
        mock_client.messages.create.side_effect = [tool_response, final_response]

        agent = Agent(api_key="test-key")
        result = agent.run("Analyze 'Hello world'")

        assert result.answer == "The document is general text."
        assert result.iterations == 2
        assert len(result.tool_calls) == 1
        assert result.tool_calls[0].tool_name == "analyze_document"
        assert result.total_input_tokens == 50
        assert result.total_output_tokens == 25

    @patch("agent.agent.Anthropic")
    def test_tool_result_contains_actual_output(self, mock_anthropic_cls: MagicMock) -> None:
        mock_client = MagicMock()
        mock_anthropic_cls.return_value = mock_client

        tool_response = _make_message(
            content=[
                ToolUseBlock(
                    type="tool_use",
                    id="toolu_1",
                    name="analyze_document",
                    input={"text": "Hello world. This is a test."},
                ),
            ],
            stop_reason="tool_use",
        )
        final_response = _make_message(
            content=[TextBlock(type="text", text="Analysis complete.")],
        )
        mock_client.messages.create.side_effect = [tool_response, final_response]

        agent = Agent(api_key="test-key")
        result = agent.run("Analyze this")

        tool_step = result.tool_calls[0]
        assert tool_step.tool_result is not None
        assert "document_type" in tool_step.tool_result
        assert "statistics" in tool_step.tool_result


class TestAgentMaxIterations:
    """Agent hits the iteration safety limit."""

    @patch("agent.agent.Anthropic")
    def test_stops_at_max_iterations(self, mock_anthropic_cls: MagicMock) -> None:
        mock_client = MagicMock()
        mock_anthropic_cls.return_value = mock_client

        # Every response wants another tool call — never gives end_turn
        infinite_tool = _make_message(
            content=[
                ToolUseBlock(
                    type="tool_use",
                    id="toolu_loop",
                    name="analyze_document",
                    input={"text": "loop"},
                ),
            ],
            stop_reason="tool_use",
        )
        mock_client.messages.create.return_value = infinite_tool

        agent = Agent(api_key="test-key")
        result = agent.run("Loop forever", max_iterations=3)

        assert "maximum iterations" in result.answer.lower()
        assert result.iterations == 3


class TestAgentErrorHandling:
    """Agent handles errors gracefully."""

    @patch("agent.agent.Anthropic")
    def test_unknown_tool_returns_error(self, mock_anthropic_cls: MagicMock) -> None:
        mock_client = MagicMock()
        mock_anthropic_cls.return_value = mock_client

        tool_response = _make_message(
            content=[
                ToolUseBlock(
                    type="tool_use",
                    id="toolu_bad",
                    name="nonexistent_tool",
                    input={},
                ),
            ],
            stop_reason="tool_use",
        )
        final_response = _make_message(
            content=[TextBlock(type="text", text="Tool not found, sorry.")],
        )
        mock_client.messages.create.side_effect = [tool_response, final_response]

        agent = Agent(api_key="test-key")
        result = agent.run("Use a fake tool")

        tool_step = result.tool_calls[0]
        assert "error" in tool_step.tool_result
        assert "Unknown tool" in tool_step.tool_result["error"]

    @patch("agent.agent.time.sleep")
    @patch("agent.agent.Anthropic")
    def test_retries_on_rate_limit(
        self, mock_anthropic_cls: MagicMock, mock_sleep: MagicMock
    ) -> None:
        mock_client = MagicMock()
        mock_anthropic_cls.return_value = mock_client

        # First call: rate limited. Second call: success.
        rate_limit_error = RateLimitError(
            message="Rate limited",
            response=MagicMock(status_code=429, headers={}),
            body=None,
        )
        success_response = _make_message(
            content=[TextBlock(type="text", text="Got through!")],
        )
        mock_client.messages.create.side_effect = [rate_limit_error, success_response]

        agent = Agent(api_key="test-key", max_retries=3)
        result = agent.run("Test retry")

        assert result.answer == "Got through!"
        assert mock_sleep.called
        assert mock_client.messages.create.call_count == 2
