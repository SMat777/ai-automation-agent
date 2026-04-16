# AI Automation Agent

An AI-powered automation agent that demonstrates **agent architecture**, **tool calling**, and **workflow automation** using Python and TypeScript.

Built as a learning project to explore how AI agents can automate real business tasks — from document analysis to data extraction pipelines.

## What This Project Demonstrates

| Skill | Technology | Where |
|-------|-----------|-------|
| AI Agent Architecture | Python, Claude API | `agent/` |
| Tool Calling & Decision Logic | Anthropic SDK, function tools | `agent/tools/` |
| Automation Workflows | TypeScript, Node.js | `automation/` |
| API Integration | REST, connectors | `automation/connectors/` |
| Testing | pytest, vitest | `tests/` |
| CI/CD | GitHub Actions | `.github/workflows/` |
| Documentation | Markdown, Architecture Docs | `docs/` |

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                        User / Trigger                        │
└─────────────────────────────┬────────────────────────────────┘
                              │
                              v
┌──────────────────────────────────────────────────────────────┐
│                     AI Agent (Python)                         │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────────────┐ │
│  │ Agent Core   │  │ Tool Router  │  │ Prompt Templates    │ │
│  │ (Decision    │──│ (Selects &   │  │ (System prompts,    │ │
│  │  Loop)       │  │  executes    │  │  few-shot examples) │ │
│  └─────────────┘  │  tools)      │  └─────────────────────┘ │
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
│                Automation Pipeline (TypeScript)                │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────────────┐ │
│  │ Connectors  │──│ Transforms   │──│ Output              │ │
│  │ (API/File)  │  │ (Clean/Map)  │  │ (Report/Notify)     │ │
│  └─────────────┘  └──────────────┘  └─────────────────────┘ │
└──────────────────────────────────────────────────────────────┘
```

**Agent** (Python): Receives a task, reasons about which tools to use, calls them, and synthesizes results.

**Automation Pipeline** (TypeScript): Orchestrates multi-step data flows — fetching from APIs, transforming data, and producing structured output.

**Integration**: The agent can trigger automation pipelines, and pipelines can feed results back to the agent for further analysis.

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 20+
- An Anthropic API key ([get one here](https://console.anthropic.com/))

### Setup

```bash
# Clone the repo
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
# Run the AI agent
python -m agent.main "Analyze this document and extract key metrics"

# Run the automation pipeline
cd automation && npm start
```

### Test

```bash
# Python tests
pytest tests/agent/ -v

# TypeScript tests
cd automation && npm test
```

## Project Structure

```
ai-automation-agent/
├── agent/                  # Python – AI Agent
│   ├── __init__.py
│   ├── main.py             # Entry point & agent loop
│   ├── agent.py            # Core agent with decision logic
│   ├── tools/              # Tool implementations
│   │   ├── __init__.py
│   │   ├── analyze.py      # Document analysis tool
│   │   ├── extract.py      # Data extraction tool
│   │   └── summarize.py    # Report summarization tool
│   └── prompts/            # Prompt templates
│       └── system.py       # System prompts
├── automation/             # TypeScript – Automation Pipeline
│   ├── package.json
│   ├── tsconfig.json
│   ├── src/
│   │   ├── index.ts        # Pipeline entry point
│   │   ├── pipeline.ts     # Workflow orchestration
│   │   ├── connectors/     # Data source connectors
│   │   │   └── api.ts      # REST API connector
│   │   └── transforms/     # Data transformations
│   │       └── clean.ts    # Data cleaning utilities
├── docs/                   # Documentation
│   ├── ARCHITECTURE.md     # Technical architecture deep-dive
│   └── LEARNING.md         # Learning journal
├── tests/                  # Test suites
│   ├── agent/              # Python agent tests
│   │   └── test_agent.py
│   └── automation/         # TypeScript pipeline tests
│       └── pipeline.test.ts
├── .github/                # GitHub configuration
│   ├── workflows/          # CI/CD pipelines
│   │   └── ci.yml
│   ├── ISSUE_TEMPLATE/     # Structured issue templates
│   └── PULL_REQUEST_TEMPLATE/
├── .env.example            # Environment variable template
├── .gitignore
├── requirements.txt        # Python dependencies
├── LICENSE
├── CONTRIBUTING.md         # How to contribute & workflow docs
└── README.md               # This file
```

## Development Workflow

This project follows a structured Git workflow:

1. **Issues** track all work — features, bugs, learning tasks
2. **Feature branches** (`feature/agent-core`, `feature/automation-pipeline`)
3. **Pull requests** with descriptions, test results, and learning reflections
4. **CI/CD** validates every push (linting, tests, type checks)
5. **Milestones** group issues into development phases
6. **Releases** mark completed milestones

See [CONTRIBUTING.md](CONTRIBUTING.md) for the full workflow guide.

## Development Phases

- **Phase 0**: Project setup, CI/CD, documentation structure
- **Phase 1**: Python AI Agent core (agent loop + 2 tools)
- **Phase 2**: TypeScript automation pipeline (1 workflow)
- **Phase 3**: Integration (agent triggers pipeline, pipeline feeds agent)
- **Phase 4**: Tests, documentation polish, v1.0 release

## Tech Stack

**Agent (Python)**
- [Anthropic Python SDK](https://github.com/anthropics/anthropic-sdk-python) — Claude API with tool use
- [python-dotenv](https://github.com/theskumar/python-dotenv) — Environment management
- [pytest](https://docs.pytest.org/) — Testing

**Automation (TypeScript)**
- [TypeScript](https://www.typescriptlang.org/) — Type-safe automation
- [tsx](https://github.com/privatenumber/tsx) — TypeScript execution
- [vitest](https://vitest.dev/) — Fast testing
- [zod](https://zod.dev/) — Runtime validation

## License

MIT — see [LICENSE](LICENSE) for details.

---

Built by [Simon Mathiasen](https://github.com/SMat777) as a learning project exploring AI agent architecture and automation workflows.
