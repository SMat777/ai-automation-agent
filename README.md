# AI Automation Agent

[![CI](https://github.com/SMat777/ai-automation-agent/actions/workflows/ci.yml/badge.svg)](https://github.com/SMat777/ai-automation-agent/actions/workflows/ci.yml)
[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/)
[![TypeScript 5.7](https://img.shields.io/badge/typescript-5.7-blue.svg)](https://www.typescriptlang.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

An intelligent automation system that combines AI-driven reasoning with composable data pipelines to automate document analysis, data extraction, and reporting workflows.

## What It Does

- **AI Agent** receives a task in natural language, reasons about which tools to use, executes them, and synthesizes results into a structured report
- **Automation Pipeline** fetches data from REST APIs, applies composable transformations (clean, filter, map, aggregate, format), and produces structured output
- **Integration** — the agent triggers pipelines at runtime, and pipeline results feed back into the agent for further analysis, creating a complete task-to-report loop

### Example

```bash
# Run the AI agent with a task
python -m agent.main "Analyze this document and extract key metrics"

# Run the automation pipeline directly
cd automation && npm start

# Run end-to-end demo (agent + pipeline)
python demo.py
```

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                       User / Trigger                         │
└─────────────────────────────┬────────────────────────────────┘
                              │
                              v
┌──────────────────────────────────────────────────────────────┐
│                      AI Agent (Python)                        │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────────────┐ │
│  │ Agent Core   │  │ Tool Router  │  │ Prompt Templates    │ │
│  │ (ReAct loop) │──│ (Select and  │  │ (System prompts,    │ │
│  │              │  │  execute)    │  │  few-shot examples) │ │
│  └─────────────┘  │              │  └─────────────────────┘ │
│                    └──────┬───────┘                           │
│                           │                                   │
│  ┌────────────┐  ┌───────┴──────┐  ┌───────────────────┐    │
│  │ Analyze    │  │ Extract      │  │ Summarize         │    │
│  │ Document   │  │ Data         │  │ Report            │    │
│  └────────────┘  └──────────────┘  └───────────────────┘    │
└──────────────────────────────┬───────────────────────────────┘
                               │
                               v
┌──────────────────────────────────────────────────────────────┐
│                 Automation Pipeline (TypeScript)               │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────────────┐ │
│  │ Connectors  │──│ Transforms   │──│ Output              │ │
│  │ (API/File)  │  │ (Clean/Map)  │  │ (Report/Notify)     │ │
│  └─────────────┘  └──────────────┘  └─────────────────────┘ │
└──────────────────────────────────────────────────────────────┘
```

**Agent** (Python): Implements a ReAct (Reasoning + Acting) decision loop. The agent iteratively reasons about the task, selects tools, observes results, and decides the next action until it produces a final answer.

**Pipeline** (TypeScript): Orchestrates multi-step data transformations with full type safety via Zod. Supports 5 composable transforms: clean, filter, map, aggregate, and format.

**Integration**: The agent triggers automation pipelines via the `run_pipeline` tool. Pipeline results are fed back to the agent for further analysis, enabling complex multi-step workflows.

## Tech Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Agent core | Python, [Anthropic SDK](https://github.com/anthropics/anthropic-sdk-python) | ReAct loop with Claude API tool use |
| Agent tools | Python | Document analysis, data extraction, summarization |
| Pipeline | TypeScript, [Zod](https://zod.dev/) | Data transformation with runtime validation |
| API connector | TypeScript | REST client with retry and exponential backoff |
| Testing | [pytest](https://docs.pytest.org/), [vitest](https://vitest.dev/) | 79 tests across both components |
| CI/CD | [GitHub Actions](https://github.com/features/actions) | Lint, type-check, and test on every push |

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 20+
- Anthropic API key ([get one here](https://console.anthropic.com/))

### Setup

```bash
git clone https://github.com/SMat777/ai-automation-agent.git
cd ai-automation-agent

# Python setup
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# TypeScript setup
cd automation
npm install
cd ..

# Environment
cp .env.example .env
# Add your ANTHROPIC_API_KEY to .env
```

### Run

```bash
# AI agent
python -m agent.main "Analyze this document and extract key metrics"

# Automation pipeline
cd automation && npm start

# End-to-end demo (agent + pipeline)
python demo.py
```

### Test

```bash
# Python tests (43 tests)
pytest tests/agent/ -v

# TypeScript tests (36 tests)
cd automation && npm test
```

## Project Structure

```
ai-automation-agent/
├── agent/                  # Python — AI Agent
│   ├── main.py             # Entry point and agent loop
│   ├── agent.py            # Agent core with decision logic
│   ├── tools/              # Tool implementations
│   │   ├── analyze.py      # Document analysis (type, entities, key points)
│   │   ├── extract.py      # Data extraction (key-value, table, list)
│   │   ├── summarize.py    # Report summarization
│   │   └── pipeline.py     # Pipeline trigger tool
│   └── prompts/
│       └── system.py       # System prompts
├── automation/             # TypeScript — Automation Pipeline
│   ├── src/
│   │   ├── index.ts        # Pipeline entry point and demo
│   │   ├── pipeline.ts     # Workflow orchestration
│   │   ├── connectors/
│   │   │   └── api.ts      # REST API connector with retry
│   │   └── transforms/     # Data transformations
│   │       ├── clean.ts    # Deduplication and null removal
│   │       ├── filter.ts   # Range-based filtering
│   │       ├── map.ts      # Field selection and computed fields
│   │       ├── aggregate.ts # Grouping and aggregation
│   │       └── format.ts   # Markdown/CSV formatting
├── tests/                  # Test suites
│   ├── agent/              # Python agent tests (43 tests)
│   └── automation/         # TypeScript pipeline tests (36 tests)
├── docs/
│   └── ARCHITECTURE.md     # Technical architecture documentation
├── demo.py                 # End-to-end integration demo
├── .github/workflows/
│   └── ci.yml              # CI/CD pipeline (lint, test, typecheck)
├── requirements.txt        # Python dependencies
├── CONTRIBUTING.md         # Development workflow
└── LICENSE                 # MIT
```

## License

MIT — see [LICENSE](LICENSE) for details.
