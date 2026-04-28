"""Tests for the Agent class — verifies tool routing, result structure, and error handling."""

from agent.agent import AgentResult, AgentStep
from agent.tools import TOOLS, TOOL_HANDLERS


class TestToolRegistry:
    """Verify that all tools are properly registered."""

    def test_all_tools_have_handlers(self) -> None:
        for tool in TOOLS:
            assert tool["name"] in TOOL_HANDLERS, (
                f"Tool '{tool['name']}' has no handler in TOOL_HANDLERS"
            )

    def test_all_handlers_have_tools(self) -> None:
        tool_names = {tool["name"] for tool in TOOLS}
        for handler_name in TOOL_HANDLERS:
            assert handler_name in tool_names, (
                f"Handler '{handler_name}' has no tool definition in TOOLS"
            )

    def test_tools_have_required_fields(self) -> None:
        for tool in TOOLS:
            assert "name" in tool
            assert "description" in tool
            assert "input_schema" in tool
            assert tool["input_schema"]["type"] == "object"

    def test_tool_count(self) -> None:
        assert len(TOOLS) == 5
        assert len(TOOL_HANDLERS) == 5


class TestAgentResult:
    """Verify AgentResult dataclass behavior."""

    def test_empty_result(self) -> None:
        result = AgentResult(answer="test")
        assert result.answer == "test"
        assert result.steps == []
        assert result.tool_calls == []
        assert result.total_input_tokens == 0
        assert result.iterations == 0

    def test_tool_calls_filters_steps(self) -> None:
        result = AgentResult(
            answer="done",
            steps=[
                AgentStep(iteration=1, action="think", text="reasoning"),
                AgentStep(iteration=1, action="tool_call", tool_name="analyze_document"),
                AgentStep(iteration=2, action="think", text="more reasoning"),
                AgentStep(iteration=2, action="final_answer", text="done"),
            ],
        )
        assert len(result.tool_calls) == 1
        assert result.tool_calls[0].tool_name == "analyze_document"

    def test_tracks_token_usage(self) -> None:
        result = AgentResult(
            answer="done",
            total_input_tokens=500,
            total_output_tokens=200,
        )
        assert result.total_input_tokens == 500
        assert result.total_output_tokens == 200


class TestAgentStep:
    """Verify AgentStep dataclass."""

    def test_defaults(self) -> None:
        step = AgentStep(iteration=1, action="think")
        assert step.tool_name is None
        assert step.tool_input is None
        assert step.tool_result is None
        assert step.text is None
        assert step.duration_ms == 0

    def test_tool_call_step(self) -> None:
        step = AgentStep(
            iteration=2,
            action="tool_call",
            tool_name="extract_data",
            tool_input={"text": "hello", "fields": ["name"]},
            tool_result={"extracted": {"name": "Alice"}},
            duration_ms=15,
        )
        assert step.tool_name == "extract_data"
        assert step.duration_ms == 15
