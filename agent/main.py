"""Entry point for the AI Automation Agent."""

import os
import sys

from dotenv import load_dotenv

from agent.agent import Agent


def main() -> None:
    """Run the agent with a task from command-line arguments."""
    load_dotenv()

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

    print("--- Agent Result ---")
    print(result)


if __name__ == "__main__":
    main()
