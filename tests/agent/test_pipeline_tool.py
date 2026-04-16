"""Tests for the pipeline tool — verifies error handling for subprocess calls."""

import subprocess
from unittest.mock import patch, MagicMock

from agent.tools.pipeline import handle_run_pipeline, PIPELINE_TOOL


class TestPipelineToolDefinition:
    def test_has_required_fields(self) -> None:
        assert PIPELINE_TOOL["name"] == "run_pipeline"
        assert "description" in PIPELINE_TOOL
        assert PIPELINE_TOOL["input_schema"]["type"] == "object"
        assert "task" in PIPELINE_TOOL["input_schema"]["properties"]


class TestPipelineToolErrors:
    @patch("agent.tools.pipeline.subprocess.run")
    @patch("agent.tools.pipeline.Path")
    def test_handles_timeout(self, mock_path: MagicMock, mock_run: MagicMock) -> None:
        mock_path.return_value.parent.parent.parent.__truediv__.return_value.__truediv__.return_value.exists.return_value = True
        mock_run.side_effect = subprocess.TimeoutExpired("cmd", 30)

        result = handle_run_pipeline("test task")
        assert "error" in result
        assert "timed out" in result["error"]

    @patch("agent.tools.pipeline.subprocess.run")
    @patch("agent.tools.pipeline.Path")
    def test_handles_missing_node(self, mock_path: MagicMock, mock_run: MagicMock) -> None:
        mock_path.return_value.parent.parent.parent.__truediv__.return_value.__truediv__.return_value.exists.return_value = True
        mock_run.side_effect = FileNotFoundError()

        result = handle_run_pipeline("test task")
        assert "error" in result
        assert "Node.js" in result["error"]

    @patch("agent.tools.pipeline.subprocess.run")
    @patch("agent.tools.pipeline.Path")
    def test_handles_nonzero_exit(self, mock_path: MagicMock, mock_run: MagicMock) -> None:
        mock_path.return_value.parent.parent.parent.__truediv__.return_value.__truediv__.return_value.exists.return_value = True
        mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="Some error")

        result = handle_run_pipeline("test task")
        assert "error" in result

    @patch("agent.tools.pipeline.subprocess.run")
    @patch("agent.tools.pipeline.Path")
    def test_returns_output_on_success(self, mock_path: MagicMock, mock_run: MagicMock) -> None:
        mock_path.return_value.parent.parent.parent.__truediv__.return_value.__truediv__.return_value.exists.return_value = True
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="--- Pipeline Result ---\n| user | posts |\n--- Metadata ---\ndone",
            stderr="",
        )

        result = handle_run_pipeline("analyze posts")
        assert result["success"] is True
        assert result["task"] == "analyze posts"
        assert "user" in result["output"]
