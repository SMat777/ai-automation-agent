"""Pipeline tool — lets the agent trigger the TypeScript automation pipeline."""

from __future__ import annotations

import subprocess
from pathlib import Path

PIPELINE_TOOL = {
    "name": "run_pipeline",
    "description": (
        "Run the TypeScript automation pipeline to fetch, process, and format "
        "data from external APIs. Returns structured results including "
        "aggregated data and pipeline metadata. Use this when you need to "
        "gather and process data before analyzing it."
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
        },
        "required": ["task"],
    },
}


def handle_run_pipeline(task: str) -> dict:
    """Execute the TypeScript automation pipeline via subprocess.

    The pipeline fetches data from an API, cleans/transforms it,
    and returns aggregated results.

    Args:
        task: Description of the pipeline task (logged for context).

    Returns:
        Dictionary with pipeline output and execution metadata.
    """
    automation_dir = Path(__file__).parent.parent.parent / "automation"

    if not (automation_dir / "node_modules").exists():
        return {"error": "Pipeline dependencies not installed. Run: cd automation && npm install"}

    try:
        result = subprocess.run(
            ["npx", "tsx", "src/index.ts"],
            cwd=str(automation_dir),
            capture_output=True,
            text=True,
            timeout=30,
        )

        # Parse the output to extract the pipeline result
        output = result.stdout
        stderr = result.stderr

        if result.returncode != 0:
            return {
                "error": f"Pipeline exited with code {result.returncode}",
                "stderr": stderr[:500] if stderr else None,
            }

        # Extract the markdown table from output (between --- markers)
        lines = output.split("\n")
        result_section = False
        result_lines = []
        metadata_lines = []

        for line in lines:
            if "--- Pipeline Result ---" in line:
                result_section = True
                continue
            if "--- Metadata ---" in line:
                result_section = False
                continue
            if result_section:
                result_lines.append(line)
            elif not result_section and line.strip() and "Pipeline:" not in line:
                metadata_lines.append(line)

        pipeline_output = "\n".join(result_lines).strip()

        return {
            "task": task,
            "output": pipeline_output if pipeline_output else output[:1000],
            "success": True,
        }

    except subprocess.TimeoutExpired:
        return {"error": "Pipeline timed out after 30 seconds"}
    except FileNotFoundError:
        return {"error": "Node.js/npx not found. Ensure Node.js is installed."}
    except Exception as e:
        return {"error": f"Pipeline execution failed: {str(e)}"}
