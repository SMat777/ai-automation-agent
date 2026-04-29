"""Tests for the workflow engine — validation, execution, variable passing, error handling."""

from __future__ import annotations

from typing import Any
from unittest.mock import patch

import pytest

from app.services.workflow.engine import WorkflowEngine


# ── Helpers ──────────────────────────────────────────────────────────────────

def _mock_handler_echo(**kwargs: Any) -> dict[str, Any]:
    """Test handler that echoes its input back."""
    return {"echo": kwargs}


def _mock_handler_fail(**kwargs: Any) -> dict[str, Any]:
    """Test handler that always raises."""
    msg = "tool exploded"
    raise RuntimeError(msg)


MOCK_HANDLERS = {
    "echo_tool": _mock_handler_echo,
    "fail_tool": _mock_handler_fail,
}


# ── Validation ───────────────────────────────────────────────────────────────


class TestValidation:
    """WorkflowEngine.validate rejects bad definitions before execution."""

    def test_rejects_empty_steps(self) -> None:
        definition = {"steps": [], "on_error": "stop"}
        engine = WorkflowEngine(tool_handlers=MOCK_HANDLERS)

        errors = engine.validate(definition)

        assert len(errors) > 0
        assert any("step" in e.lower() for e in errors)

    def test_rejects_unknown_tool(self) -> None:
        definition = {
            "steps": [
                {"step_id": "s1", "tool_name": "nonexistent_tool", "input_template": {}},
            ],
            "on_error": "stop",
        }
        engine = WorkflowEngine(tool_handlers=MOCK_HANDLERS)

        errors = engine.validate(definition)

        assert len(errors) > 0
        assert any("nonexistent_tool" in e for e in errors)

    def test_rejects_invalid_on_error(self) -> None:
        definition = {
            "steps": [
                {"step_id": "s1", "tool_name": "echo_tool", "input_template": {}},
            ],
            "on_error": "explode",
        }
        engine = WorkflowEngine(tool_handlers=MOCK_HANDLERS)

        errors = engine.validate(definition)

        assert len(errors) > 0
        assert any("on_error" in e for e in errors)

    def test_rejects_missing_step_id(self) -> None:
        definition = {
            "steps": [
                {"tool_name": "echo_tool", "input_template": {}},
            ],
            "on_error": "stop",
        }
        engine = WorkflowEngine(tool_handlers=MOCK_HANDLERS)

        errors = engine.validate(definition)

        assert len(errors) > 0

    def test_rejects_duplicate_step_ids(self) -> None:
        definition = {
            "steps": [
                {"step_id": "same", "tool_name": "echo_tool", "input_template": {}},
                {"step_id": "same", "tool_name": "echo_tool", "input_template": {}},
            ],
            "on_error": "stop",
        }
        engine = WorkflowEngine(tool_handlers=MOCK_HANDLERS)

        errors = engine.validate(definition)

        assert len(errors) > 0
        assert any("duplicate" in e.lower() for e in errors)

    def test_accepts_valid_definition(self) -> None:
        definition = {
            "steps": [
                {"step_id": "s1", "tool_name": "echo_tool", "input_template": {"text": "hello"}},
            ],
            "on_error": "stop",
        }
        engine = WorkflowEngine(tool_handlers=MOCK_HANDLERS)

        errors = engine.validate(definition)

        assert errors == []


# ── Single-step execution ────────────────────────────────────────────────────


class TestSingleStepExecution:
    """Engine executes a single-step workflow correctly."""

    def test_executes_single_step(self) -> None:
        definition = {
            "steps": [
                {"step_id": "greet", "tool_name": "echo_tool", "input_template": {"text": "hello"}},
            ],
            "on_error": "stop",
        }
        engine = WorkflowEngine(tool_handlers=MOCK_HANDLERS)

        result = engine.execute(definition, workflow_input={})

        assert result["status"] == "completed"
        assert len(result["steps"]) == 1
        assert result["steps"][0]["step_id"] == "greet"
        assert result["steps"][0]["status"] == "success"
        assert result["steps"][0]["output"]["echo"] == {"text": "hello"}

    def test_result_includes_total_duration(self) -> None:
        definition = {
            "steps": [
                {"step_id": "s1", "tool_name": "echo_tool", "input_template": {}},
            ],
            "on_error": "stop",
        }
        engine = WorkflowEngine(tool_handlers=MOCK_HANDLERS)

        result = engine.execute(definition, workflow_input={})

        assert "total_duration_ms" in result
        assert isinstance(result["total_duration_ms"], int)


# ── Variable passing ─────────────────────────────────────────────────────────


class TestVariablePassing:
    """Engine resolves $input, $prev, and $steps.X references."""

    def test_input_variable(self) -> None:
        """$input.text resolves to the workflow's top-level input."""
        definition = {
            "steps": [
                {"step_id": "s1", "tool_name": "echo_tool", "input_template": {"text": "$input.text"}},
            ],
            "on_error": "stop",
        }
        engine = WorkflowEngine(tool_handlers=MOCK_HANDLERS)

        result = engine.execute(definition, workflow_input={"text": "from user"})

        assert result["steps"][0]["output"]["echo"] == {"text": "from user"}

    def test_prev_variable(self) -> None:
        """$prev.echo.text resolves to the previous step's output."""
        definition = {
            "steps": [
                {"step_id": "s1", "tool_name": "echo_tool", "input_template": {"text": "first"}},
                {"step_id": "s2", "tool_name": "echo_tool", "input_template": {"text": "$prev.echo.text"}},
            ],
            "on_error": "stop",
        }
        engine = WorkflowEngine(tool_handlers=MOCK_HANDLERS)

        result = engine.execute(definition, workflow_input={})

        assert result["steps"][1]["output"]["echo"] == {"text": "first"}

    def test_steps_variable(self) -> None:
        """$steps.s1.echo.text resolves to a named step's output."""
        definition = {
            "steps": [
                {"step_id": "s1", "tool_name": "echo_tool", "input_template": {"text": "original"}},
                {"step_id": "s2", "tool_name": "echo_tool", "input_template": {"other": "filler"}},
                {"step_id": "s3", "tool_name": "echo_tool", "input_template": {"text": "$steps.s1.echo.text"}},
            ],
            "on_error": "stop",
        }
        engine = WorkflowEngine(tool_handlers=MOCK_HANDLERS)

        result = engine.execute(definition, workflow_input={})

        # s3 should reference s1's output, skipping s2
        assert result["steps"][2]["output"]["echo"] == {"text": "original"}

    def test_unresolved_variable_returns_error_string(self) -> None:
        """An invalid variable path results in a descriptive error string, not a crash."""
        definition = {
            "steps": [
                {"step_id": "s1", "tool_name": "echo_tool", "input_template": {"text": "$input.nonexistent"}},
            ],
            "on_error": "stop",
        }
        engine = WorkflowEngine(tool_handlers=MOCK_HANDLERS)

        result = engine.execute(definition, workflow_input={})

        # The step should still execute — the unresolved var becomes an error marker
        output_text = result["steps"][0]["output"]["echo"]["text"]
        assert "UNRESOLVED" in output_text or output_text is None


# ── Error strategies ─────────────────────────────────────────────────────────


class TestErrorStrategies:
    """on_error controls whether the workflow stops or skips on failure."""

    def test_stop_aborts_on_failure(self) -> None:
        definition = {
            "steps": [
                {"step_id": "s1", "tool_name": "fail_tool", "input_template": {}},
                {"step_id": "s2", "tool_name": "echo_tool", "input_template": {"text": "never reached"}},
            ],
            "on_error": "stop",
        }
        engine = WorkflowEngine(tool_handlers=MOCK_HANDLERS)

        result = engine.execute(definition, workflow_input={})

        assert result["status"] == "error"
        assert len(result["steps"]) == 1
        assert result["steps"][0]["status"] == "error"
        assert "tool exploded" in result["steps"][0]["error"]

    def test_skip_continues_after_failure(self) -> None:
        definition = {
            "steps": [
                {"step_id": "s1", "tool_name": "fail_tool", "input_template": {}},
                {"step_id": "s2", "tool_name": "echo_tool", "input_template": {"text": "still runs"}},
            ],
            "on_error": "skip",
        }
        engine = WorkflowEngine(tool_handlers=MOCK_HANDLERS)

        result = engine.execute(definition, workflow_input={})

        assert result["status"] == "completed"
        assert len(result["steps"]) == 2
        assert result["steps"][0]["status"] == "error"
        assert result["steps"][1]["status"] == "success"
        assert result["steps"][1]["output"]["echo"] == {"text": "still runs"}

    def test_skip_provides_empty_output_for_failed_step(self) -> None:
        """When a step fails with on_error=skip, $prev resolves to empty dict."""
        definition = {
            "steps": [
                {"step_id": "s1", "tool_name": "fail_tool", "input_template": {}},
                {"step_id": "s2", "tool_name": "echo_tool", "input_template": {"ref": "$prev"}},
            ],
            "on_error": "skip",
        }
        engine = WorkflowEngine(tool_handlers=MOCK_HANDLERS)

        result = engine.execute(definition, workflow_input={})

        assert result["steps"][1]["status"] == "success"
        # $prev for a failed step should resolve to empty dict
        assert result["steps"][1]["output"]["echo"]["ref"] == {}


# ── Validation before execution ──────────────────────────────────────────────


class TestExecutionValidation:
    """Engine validates definitions before running them."""

    def test_execute_rejects_invalid_definition(self) -> None:
        definition = {"steps": [], "on_error": "stop"}
        engine = WorkflowEngine(tool_handlers=MOCK_HANDLERS)

        result = engine.execute(definition, workflow_input={})

        assert result["status"] == "validation_error"
        assert "errors" in result
