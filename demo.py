"""End-to-end demo: Agent triggers pipeline, analyzes results.

This demonstrates the full integration:
1. Agent receives a task
2. Agent decides to call the pipeline tool
3. Pipeline fetches, transforms, and aggregates data
4. Agent analyzes the pipeline output
5. Agent produces a final human-readable report

Usage:
    python demo.py                  # Standard (sync) mode
    python demo.py --stream         # Streaming mode (real-time output)
    python demo.py "Custom task"    # Custom task

Requires:
    - ANTHROPIC_API_KEY in .env
    - npm install in automation/
"""

import argparse
import logging
import os
import sys

from dotenv import load_dotenv

from agent.agent import Agent

DEFAULT_TASK = (
    "I need a report on user posting activity. "
    "Run the data pipeline to fetch and aggregate post data, "
    "then analyze the results and give me a summary of which users "
    "are most active and what the overall posting patterns look like."
)


def main() -> None:
    load_dotenv()

    parser = argparse.ArgumentParser(description="AI Automation Agent Demo")
    parser.add_argument("task", nargs="?", default=DEFAULT_TASK, help="Task for the agent")
    parser.add_argument("--stream", action="store_true", help="Enable streaming output")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: Set ANTHROPIC_API_KEY in .env")
        sys.exit(1)

    agent = Agent(api_key=api_key)

    print(f"Task: {args.task}\n")
    print("=" * 60)

    if args.stream:
        print("[Streaming mode]\n")
        stream = agent.run_stream(args.task)
        for chunk in stream:
            print(chunk, end="", flush=True)
        print()
        result = stream.result
    else:
        result = agent.run(args.task)

    if result:
        print("\n" + "=" * 60)
        print("FINAL REPORT")
        print("=" * 60)
        print(result.answer)
        print("\n--- Stats ---")
        print(f"Iterations: {result.iterations}")
        print(f"Tool calls: {len(result.tool_calls)}")
        for step in result.tool_calls:
            print(f"  - {step.tool_name} ({step.duration_ms}ms)")
        print(f"Tokens: {result.total_input_tokens} in + {result.total_output_tokens} out")
        print(f"Duration: {result.total_duration_ms}ms")


if __name__ == "__main__":
    main()
