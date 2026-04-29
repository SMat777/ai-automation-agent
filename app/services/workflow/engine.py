"""Workflow execution engine.

Takes a workflow definition (dict with steps, on_error) and executes
each step sequentially, resolving variable references between steps.

Variable reference syntax:
  $input           → the entire workflow input dict
  $input.field     → a specific field from workflow input
  $prev            → the entire output of the previous step
  $prev.field      → a specific field from previous step output
  $steps.X         → the entire output of step with step_id "X"
  $steps.X.field   → a specific field from step X's output

The engine dispatches tool calls via the TOOL_HANDLERS dict, keeping
it decoupled from the agent's ReAct loop. Tools are called directly
— no LLM involved in workflow execution.
"""

from __future__ import annotations

import time
from typing import Any, Callable

VALID_ERROR_STRATEGIES = {"stop", "skip"}


class WorkflowEngine:
    """Validates and executes workflow definitions against registered tools."""

    def __init__(self, tool_handlers: dict[str, Callable[..., dict[str, Any]]]) -> None:
        self._handlers = tool_handlers

    # ── Validation ───────────────────────────────────────────────────────

    def validate(self, definition: dict[str, Any]) -> list[str]:
        """Check a workflow definition for errors. Returns a list of error messages (empty = valid)."""
        errors: list[str] = []
        steps = definition.get("steps", [])
        on_error = definition.get("on_error", "stop")

        # Must have at least one step
        if not steps:
            errors.append("Workflow must have at least one step.")
            return errors

        # on_error must be a known strategy
        if on_error not in VALID_ERROR_STRATEGIES:
            errors.append(
                f"Invalid on_error strategy '{on_error}'. Must be one of: {', '.join(sorted(VALID_ERROR_STRATEGIES))}."
            )

        seen_ids: set[str] = set()
        for i, step in enumerate(steps):
            step_id = step.get("step_id")
            tool_name = step.get("tool_name")

            # step_id is required
            if not step_id:
                errors.append(f"Step {i} is missing a 'step_id'.")
                continue

            # No duplicate step_ids
            if step_id in seen_ids:
                errors.append(f"Duplicate step_id '{step_id}'. Each step must have a unique ID.")
            seen_ids.add(step_id)

            # tool_name must exist in handlers
            if tool_name and tool_name not in self._handlers:
                errors.append(
                    f"Step '{step_id}' references unknown tool '{tool_name}'. "
                    f"Available: {', '.join(sorted(self._handlers.keys()))}."
                )
            elif not tool_name:
                errors.append(f"Step '{step_id}' is missing a 'tool_name'.")

        return errors

    # ── Execution ────────────────────────────────────────────────────────

    def execute(
        self,
        definition: dict[str, Any],
        workflow_input: dict[str, Any],
    ) -> dict[str, Any]:
        """Execute a workflow definition and return a structured result.

        Returns a dict with:
          status: "completed" | "error" | "validation_error"
          steps: list of step results
          total_duration_ms: total execution time
          errors: (only for validation_error) list of validation errors
        """
        # Validate first
        validation_errors = self.validate(definition)
        if validation_errors:
            return {
                "status": "validation_error",
                "errors": validation_errors,
                "steps": [],
                "total_duration_ms": 0,
            }

        steps_def = definition["steps"]
        on_error = definition.get("on_error", "stop")

        step_results: list[dict[str, Any]] = []
        step_outputs: dict[str, dict[str, Any]] = {}  # step_id → output
        prev_output: dict[str, Any] = {}

        total_start = time.perf_counter()

        for step_def in steps_def:
            step_id = step_def["step_id"]
            tool_name = step_def["tool_name"]
            input_template = step_def.get("input_template", {})

            # Build execution context for variable resolution
            context = _ExecutionContext(
                workflow_input=workflow_input,
                prev_output=prev_output,
                step_outputs=step_outputs,
            )

            # Resolve variable references in the input template
            resolved_input = _resolve_template(input_template, context)

            # Execute the tool
            step_start = time.perf_counter()
            try:
                handler = self._handlers[tool_name]
                output = handler(**resolved_input)
                step_results.append({
                    "step_id": step_id,
                    "tool_name": tool_name,
                    "status": "success",
                    "output": output,
                    "duration_ms": round((time.perf_counter() - step_start) * 1000),
                })
                step_outputs[step_id] = output
                prev_output = output

            except Exception as exc:
                step_result = {
                    "step_id": step_id,
                    "tool_name": tool_name,
                    "status": "error",
                    "error": str(exc),
                    "duration_ms": round((time.perf_counter() - step_start) * 1000),
                }
                step_results.append(step_result)

                if on_error == "stop":
                    return {
                        "status": "error",
                        "steps": step_results,
                        "total_duration_ms": round((time.perf_counter() - total_start) * 1000),
                    }

                # on_error == "skip": continue with empty output for this step
                step_outputs[step_id] = {}
                prev_output = {}

        return {
            "status": "completed",
            "steps": step_results,
            "total_duration_ms": round((time.perf_counter() - total_start) * 1000),
        }


# ── Variable resolution ─────────────────────────────────────────────────────


class _ExecutionContext:
    """Holds the data available for variable resolution during execution."""

    def __init__(
        self,
        workflow_input: dict[str, Any],
        prev_output: dict[str, Any],
        step_outputs: dict[str, dict[str, Any]],
    ) -> None:
        self.workflow_input = workflow_input
        self.prev_output = prev_output
        self.step_outputs = step_outputs


def _resolve_template(
    template: dict[str, Any],
    context: _ExecutionContext,
) -> dict[str, Any]:
    """Walk a template dict and resolve any $-prefixed variable references."""
    resolved: dict[str, Any] = {}
    for key, value in template.items():
        if isinstance(value, str) and value.startswith("$"):
            resolved[key] = _resolve_variable(value, context)
        elif isinstance(value, dict):
            resolved[key] = _resolve_template(value, context)
        else:
            resolved[key] = value
    return resolved


def _resolve_variable(ref: str, context: _ExecutionContext) -> Any:
    """Resolve a single variable reference like $input.field or $steps.s1.field.

    Returns the resolved value, or an UNRESOLVED marker string if the path is invalid.
    """
    parts = ref.split(".")

    if parts[0] == "$input":
        return _walk_path(context.workflow_input, parts[1:])

    if parts[0] == "$prev":
        return _walk_path(context.prev_output, parts[1:])

    if parts[0] == "$steps" and len(parts) >= 2:
        step_id = parts[1]
        step_output = context.step_outputs.get(step_id)
        if step_output is None:
            return f"UNRESOLVED: step '{step_id}' not found"
        return _walk_path(step_output, parts[2:])

    return f"UNRESOLVED: unknown variable '{ref}'"


def _walk_path(data: Any, path: list[str]) -> Any:
    """Walk a dotted path into a nested dict. Returns UNRESOLVED marker on failure."""
    current = data
    for segment in path:
        if isinstance(current, dict) and segment in current:
            current = current[segment]
        else:
            return f"UNRESOLVED: path '{'.'.join(path)}' not found"
    return current
