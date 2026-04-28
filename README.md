# AI Document Agent Platform

[![CI](https://github.com/SMat777/ai-automation-agent/actions/workflows/ci.yml/badge.svg)](https://github.com/SMat777/ai-automation-agent/actions/workflows/ci.yml)
[![Python 3.11](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![TypeScript 5.7](https://img.shields.io/badge/typescript-5.7-blue.svg)](https://www.typescriptlang.org/)
[![Tests](https://img.shields.io/badge/tests-156%20passing-green.svg)]()
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

An AI-powered platform for automated document processing, email triage, and knowledge-base search — built with a ReAct agent loop, RAG pipeline, and full observability. Works across **4 industry scenarios**: Healthcare, Finance, Legal, and Customer Service.

## What It Does

```
INGEST → REASON → ACT → TRACE

1. Documents come in (upload PDF/DOCX/EML, paste text, or send email)
2. AI agent understands, classifies, and extracts structured data
3. Agent takes action (draft replies, validate, route, produce ERP-ready output)
4. Everything is logged with timing, tokens, and cost
```

### Industry Scenarios

| Scenario | Use Case | Key Tools |
|----------|----------|-----------|
| 🏥 **Clinic Email Agent** | Read clinic emails, look up orders, draft replies | `classify_email`, `lookup_order`, `draft_email_reply` |
| 💰 **Invoice Processing** | Extract line items, validate VAT, produce ERP-ready JSON | `analyze_document`, `extract_data` |
| ⚖️ **Contract Review** | Extract key terms, flag risks, compare with knowledge base | `search_knowledge`, `analyze_document` |
| 📧 **Support Triage** | Classify urgency, search knowledge base, draft responses | `classify_email`, `search_knowledge`, `draft_email_reply` |

**Same engine, different configuration.** Each scenario uses different system prompts and tool combinations — the architecture is reusable.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  Frontend (Vanilla JS + Lucide + Chart.js)                  │
│  Dashboard · Scenarios · Upload · Chat · Knowledge Base     │
└──────────────────────┬──────────────────────────────────────┘
                       │  REST API + SSE
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  FastAPI Backend                                            │
│  /api/upload · /api/chat · /api/process · /api/scenarios    │
│  /api/stats  · /api/knowledge · /api/runs                   │
├────────────────┬────────────────────────┬───────────────────┤
│  ReAct Agent   │  RAG Engine            │  Data Pipeline    │
│  8 tools       │  ChromaDB + OpenAI     │  TypeScript + Zod │
│  Claude Sonnet │  embeddings            │  Composable       │
│  Streaming     │  Chunk → Embed → Store │  transforms       │
├────────────────┴────────────────────────┴───────────────────┤
│  SQLite / PostgreSQL — Runs · Documents · Audit Log         │
└─────────────────────────────────────────────────────────────┘
```

## Agent Tools (8)

| Tool | Purpose |
|------|---------|
| `analyze_document` | Detect document type, extract entities and structure |
| `extract_data` | Pull structured key-value data from text |
| `summarize` | Generate concise summaries (AI or extractive fallback) |
| `run_pipeline` | Execute TypeScript data pipeline via subprocess |
| `search_knowledge` | RAG search across uploaded documents |
| `classify_email` | Categorize emails by intent, priority, sentiment |
| `draft_email_reply` | Generate professional email responses |
| `lookup_order` | Check order status in the system |

## RAG Pipeline

Upload documents → chunk text → embed via OpenAI → store in ChromaDB → search with source citations.

```python
# The agent uses RAG automatically when relevant
retriever.ingest(doc_id="report-1", text=document_text, source="Q3-report.pdf")
results = retriever.search("What were the key metrics?")
context = retriever.format_context(results)  # Injected into Claude's context
```

## Quick Start

```bash
# Clone and setup
git clone https://github.com/SMat777/ai-automation-agent.git
cd ai-automation-agent
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Configure
cp .env.example .env
# Add your ANTHROPIC_API_KEY and OPENAI_API_KEY

# Initialize database
python -c "from app.db.database import init_db; init_db()"

# Run
make dev  # Starts FastAPI on http://localhost:8000
```

### TypeScript Pipeline

```bash
cd automation && npm install && npm start
```

## Testing

```bash
make test      # 156+ Python tests
make test-ts   # 36 TypeScript tests
make lint      # Ruff + mypy
```

TDD was the development workflow — tests were written before implementation for every module.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| AI Agent | Claude Sonnet 4 via Anthropic SDK, ReAct loop |
| RAG | ChromaDB, OpenAI text-embedding-3-small |
| Backend | FastAPI, SQLAlchemy 2.0, Alembic, Pydantic |
| Frontend | Vanilla JS, Lucide Icons, Chart.js (no build step) |
| Pipeline | TypeScript, Zod, composable transforms |
| Database | SQLite (dev) / PostgreSQL (prod) |
| Testing | pytest, vitest, TDD workflow |
| CI/CD | GitHub Actions, Docker |

## Project Structure

```
agent/              # ReAct agent + 8 tools
app/
  ├── routers/      # API endpoints (12 routes)
  ├── services/
  │   ├── rag/      # Chunker, embedder, vectorstore, retriever
  │   ├── extractors/  # PDF, DOCX, EML, text extractors
  │   ├── scenarios/   # Cross-industry scenario configs
  │   └── cost.py      # Token-to-USD cost calculation
  ├── models/       # SQLAlchemy models (User, Run, AuditLog, Document)
  └── db/           # Database engine + sessions
automation/         # TypeScript data pipeline
frontend/           # Vanilla JS SPA
tests/              # 156+ Python + 36 TypeScript tests
docs/               # Architecture docs + ADRs
```

## License

MIT
