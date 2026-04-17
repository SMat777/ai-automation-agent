"""Pipeline tool — lets the agent trigger TypeScript automation pipelines."""

from __future__ import annotations

import subprocess
from pathlib import Path

AVAILABLE_PIPELINES = {
    "posts": {
        "script": "src/index.ts",
        "description": "Fetch and analyze user posting activity from JSONPlaceholder API",
    },
    "github": {
        "script": "src/github-demo.ts",
        "description": "Fetch and analyze GitHub repository data for a user",
    },
}

PIPELINE_TOOL = {
    "name": "run_pipeline",
    "description": (
        "Run a TypeScript automation pipeline to fetch, process, and format "
        "data from external APIs. Returns structured results including "
        "aggregated data and pipeline metadata."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "task": {
                "type": "string",
                "description": (
                    "Description of the data pipeline task, e.g. "
                    "'fetch and summarize posts from the API'"
                ),
            },
            "pipeline": {
                "type": "string",
                "enum": list(AVAILABLE_PIPELINES.keys()),
                "description": (
                    "Which pipeline to run. "
                    "'posts' = user posting activity analysis, "
                    "'github' = GitHub repository analysis"
                ),
                "default": "posts",
            },
        },
        "required": ["task"],
    },
}


def handle_run_pipeline(task: str, pipeline: str = "posts") -> dict:
    """Execute a TypeScript automation pipeline via subprocess.

    Args:
        task: Description of the pipeline task (logged for context).
        pipeline: Which pipeline to run ('posts' or 'github').

    Returns:
        Dictionary with pipeline output and execution metadata.
    """
    if pipeline not in AVAILABLE_PIPELINES:
        return {
            "error": f"Unknown pipeline '{pipeline}'. Available: {list(AVAILABLE_PIPELINES.keys())}",
        }

    pipeline_config = AVAILABLE_PIPELINES[pipeline]
    automation_dir = Path(__file__).parent.parent.parent / "automation"

    if not (automation_dir / "node_modules").exists():
        return {"error": "Pipeline dependencies not installed. Run: cd automation && npm install"}

    try:
        result = subprocess.run(
            ["npx", "tsx", pipeline_config["script"]],
            cwd=str(automation_dir),
            capture_output=True,
            text=True,
            timeout=30,
        )

        output = result.stdout
        stderr = result.stderr

        if result.returncode != 0:
            return {
                "error": f"Pipeline exited with code {result.returncode}",
                "stderr": stderr[:500] if stderr else None,
            }

        # Extract the result section from output (between --- markers)
        lines = output.split("\n")
        result_section = False
        result_lines = []

        for line in lines:
            if "--- Pipeline Result ---" in line:
                result_section = True
                continue
            if "--- Metadata ---" in line:
                result_section = False
                continue
            if result_section:
                result_lines.append(line)

        pipeline_output = "\n".join(result_lines).strip()

        return {
            "task": task,
            "pipeline": pipeline,
            "output": pipeline_output if pipeline_output else output[:1000],
            "success": True,
        }

    except subprocess.TimeoutExpired:
        return {"error": "Pipeline timed out after 30 seconds"}
    except FileNotFoundError:
        return {"error": "Node.js/npx not found. Ensure Node.js is installed."}
    except Exception as e:
        return {"error": f"Pipeline execution failed: {str(e)}"}
