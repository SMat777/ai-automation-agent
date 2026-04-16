"""Tests for the Agent class — verifies tool routing and error handling."""

from agent.tools import TOOLS, TOOL_HANDLERS


class TestToolRegistry:
    """Verify that all tools are properly registered."""

    def test_all_tools_have_handlers(self) -> None:
        """Every tool defined in TOOLS must have a corresponding handler."""
        for tool in TOOLS:
            assert tool["name"] in TOOL_HANDLERS, (
                f"Tool '{tool['name']}' has no handler in TOOL_HANDLERS"
            )

    def test_all_handlers_have_tools(self) -> None:
        """Every handler must have a corresponding tool definition."""
        tool_names = {tool["name"] for tool in TOOLS}
        for handler_name in TOOL_HANDLERS:
            assert handler_name in tool_names, (
                f"Handler '{handler_name}' has no tool definition in TOOLS"
            )

    def test_tools_have_required_fields(self) -> None:
        """Every tool must have name, description, and input_schema."""
        for tool in TOOLS:
            assert "name" in tool
            assert "description" in tool
            assert "input_schema" in tool
            assert tool["input_schema"]["type"] == "object"

    def test_tool_count(self) -> None:
        """Sanity check: we expect 3 tools in Phase 0."""
        assert len(TOOLS) == 3
        assert len(TOOL_HANDLERS) == 3
