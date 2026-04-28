# AI Automation Agent — Project Contract

## What This Is

AI Document Agent Platform — automated document processing and email triage with AI agents, RAG-powered knowledge base, and full observability. Cross-industry: healthcare, finance, legal, customer service.

## Tech Stack

- **Backend:** Python 3.11+, FastAPI, SQLAlchemy 2.0, Alembic, Anthropic SDK
- **AI:** Claude Sonnet via ReAct agent loop, OpenAI embeddings, ChromaDB
- **Pipeline:** TypeScript, Zod, composable transforms
- **Frontend:** Vanilla JS (no build step), Chart.js, Lucide Icons
- **Testing:** pytest (Python), vitest (TypeScript), TDD workflow
- **DB:** SQLite (dev), PostgreSQL (prod)

## Conventions

- English in all code, variables, functions, docs, commits
- Danish in plans, discussions, explanations
- TDD: tests first, then implementation
- Commits: natural language, no type-prefixes, specific file staging
- Branch: `feature/platform-upgrade` (current work)

## Key Directories

```
agent/          — ReAct agent + tools
app/            — FastAPI application (routers, services, models, db)
automation/     — TypeScript data pipeline
frontend/       — Vanilla JS SPA (served by FastAPI)
tests/          — Python + TypeScript tests
docs/           — Architecture docs + ADRs
scripts/        — Seed data, utilities
```

## Running

```bash
source .venv/bin/activate
make dev          # Start FastAPI server
make test         # Run all Python tests
make test-ts      # Run TypeScript tests
make lint         # Ruff + mypy
```

## Current Phase

Platform upgrade: RAG engine, document upload, email agent, scenarios, observability, frontend redesign.
