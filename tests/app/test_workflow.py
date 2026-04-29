"""Tests for the workflow engine — validation, execution, variable passing, error handling, and API."""

from __future__ import annotations

from typing import Any
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import get_db
from app.db.base import Base
from app.main import app
from app.models.workflow import Workflow, WorkflowStep
from app.services.workflow.engine import WorkflowEngine
from app.services.workflow.seed import seed_preset_workflows


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


# ── API endpoint tests ───────────────────────────────────────────────────────


@pytest.fixture()
def _api_engine():
    """In-memory SQLite engine shared across threads via StaticPool."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture()
def api_db(_api_engine) -> Session:
    """Session for seeding test data (same DB as the test client)."""
    TestSession = sessionmaker(bind=_api_engine, expire_on_commit=False)
    session = TestSession()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def client(_api_engine) -> TestClient:
    """Test client with DB dependency override via StaticPool."""
    TestSession = sessionmaker(bind=_api_engine, expire_on_commit=False)

    def _override_db():
        session = TestSession()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = _override_db
    yield TestClient(app)
    app.dependency_overrides.clear()


def _seed_workflow(db: Session, *, is_preset: bool = False) -> Workflow:
    """Insert a test workflow with one echo_tool step."""
    workflow = Workflow(name="Test Workflow", description="For testing", on_error="stop", is_preset=is_preset)
    workflow.steps.append(
        WorkflowStep(step_order=0, step_id="s1", tool_name="classify_email", input_template={"email_text": "$input.text"})
    )
    db.add(workflow)
    db.commit()
    db.refresh(workflow)
    return workflow


class TestWorkflowAPI:
    """REST API endpoints for workflows."""

    def test_list_workflows_empty(self, client: TestClient) -> None:
        response = client.get("/api/workflows")

        assert response.status_code == 200
        assert response.json() == {"workflows": []}

    def test_create_workflow(self, client: TestClient) -> None:
        response = client.post("/api/workflows", json={
            "name": "My Workflow",
            "description": "Test workflow",
            "on_error": "stop",
            "steps": [
                {"step_id": "s1", "tool_name": "classify_email", "input_template": {"email_text": "hello"}},
            ],
        })

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "My Workflow"
        assert len(data["steps"]) == 1
        assert data["is_preset"] is False

    def test_create_workflow_rejects_unknown_tool(self, client: TestClient) -> None:
        response = client.post("/api/workflows", json={
            "name": "Bad Workflow",
            "steps": [
                {"step_id": "s1", "tool_name": "nonexistent_tool", "input_template": {}},
            ],
        })

        assert response.status_code == 422

    def test_get_workflow(self, client: TestClient, api_db: Session) -> None:
        workflow = _seed_workflow(api_db)

        response = client.get(f"/api/workflows/{workflow.id}")

        assert response.status_code == 200
        assert response.json()["name"] == "Test Workflow"

    def test_get_workflow_not_found(self, client: TestClient) -> None:
        response = client.get("/api/workflows/999")

        assert response.status_code == 404

    def test_delete_workflow(self, client: TestClient, api_db: Session) -> None:
        workflow = _seed_workflow(api_db, is_preset=False)

        response = client.delete(f"/api/workflows/{workflow.id}")

        assert response.status_code == 204

    def test_delete_preset_workflow_forbidden(self, client: TestClient, api_db: Session) -> None:
        workflow = _seed_workflow(api_db, is_preset=True)

        response = client.delete(f"/api/workflows/{workflow.id}")

        assert response.status_code == 403

    @patch("app.routers.workflows.TOOL_HANDLERS", MOCK_HANDLERS)
    @patch("app.routers.workflows._engine", WorkflowEngine(tool_handlers=MOCK_HANDLERS))
    def test_run_workflow(self, client: TestClient, api_db: Session) -> None:
        """Run a workflow with a mock tool handler."""
        workflow = Workflow(name="Echo Workflow", description="", on_error="stop", is_preset=False)
        workflow.steps.append(
            WorkflowStep(step_order=0, step_id="s1", tool_name="echo_tool", input_template={"text": "$input.message"})
        )
        api_db.add(workflow)
        api_db.commit()
        api_db.refresh(workflow)

        response = client.post(
            f"/api/workflows/{workflow.id}/run",
            json={"input": {"message": "hello world"}},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["status"] == "completed"
        assert data["data"]["steps"][0]["output"]["echo"] == {"text": "hello world"}

    def test_run_workflow_not_found(self, client: TestClient) -> None:
        response = client.post("/api/workflows/999/run", json={"input": {}})

        assert response.status_code == 404


# ── Seed tests ───────────────────────────────────────────────────────────────


class TestSeedPresetWorkflows:
    """Preset workflows are seeded correctly."""

    def test_seeds_three_preset_workflows(self, db_session: Session) -> None:
        count = seed_preset_workflows(db_session)

        assert count == 3
        workflows = db_session.query(Workflow).filter(Workflow.is_preset.is_(True)).all()
        assert len(workflows) == 3

        names = {w.name for w in workflows}
        assert "Document Processing" in names
        assert "Email Triage" in names
        assert "Research & Summarize" in names

    def test_seed_is_idempotent(self, db_session: Session) -> None:
        """Running seed twice does not duplicate workflows."""
        first = seed_preset_workflows(db_session)
        second = seed_preset_workflows(db_session)

        assert first == 3
        assert second == 0
        total = db_session.query(Workflow).filter(Workflow.is_preset.is_(True)).count()
        assert total == 3

    def test_preset_workflows_have_steps(self, db_session: Session) -> None:
        seed_preset_workflows(db_session)

        workflows = db_session.query(Workflow).filter(Workflow.is_preset.is_(True)).all()
        for w in workflows:
            assert len(w.steps) >= 2, f"Workflow '{w.name}' should have at least 2 steps"
