"""Entry point for the AI Automation Agent."""

import logging
import os
import sys

from dotenv import load_dotenv

from agent.agent import Agent


def setup_logging() -> None:
    """Configure logging based on LOG_LEVEL environment variable."""
    level = os.getenv("LOG_LEVEL", "INFO").upper()
    logging.basicConfig(
        level=getattr(logging, level, logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )


def main() -> None:
    """Run the agent with a task from command-line arguments."""
    load_dotenv()
    setup_logging()

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: ANTHROPIC_API_KEY not set. Copy .env.example to .env and add your key.")
        sys.exit(1)

    model = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")

    if len(sys.argv) < 2:
        print("Usage: python -m agent.main \"<your task>\"")
        print("Example: python -m agent.main \"Analyze this text and extract key metrics\"")
        sys.exit(1)

    task = " ".join(sys.argv[1:])
    print(f"Task: {task}\n")

    agent = Agent(api_key=api_key, model=model)
    result = agent.run(task)

    print("\n--- Agent Result ---")
    print(result.answer)
    print("\n--- Metadata ---")
    print(f"Iterations: {result.iterations}")
    print(f"Tool calls: {len(result.tool_calls)}")
    print(f"Tokens: {result.total_input_tokens} in + {result.total_output_tokens} out")
    print(f"Duration: {result.total_duration_ms}ms")


if __name__ == "__main__":
    main()
