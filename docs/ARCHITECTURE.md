# Architecture

> **Status:** Living document. Updated at the end of each upgrade phase.
> Last update: 2026-04-18 (Fase 0).

## Overview

The project is a production-oriented showcase of AI-assisted document processing,
built from three cooperating components:

1. **AI Agent** (Python) — ReAct reasoning loop over a set of composable tools.
2. **Automation Pipeline** (TypeScript) — Pipe-and-filter data workflow with Zod validation.
3. **Web Application** (FastAPI + vanilla JS SPA) — HTTP API + browser UI that ties everything together.

All three are designed to run standalone *and* in composition. The agent can trigger
the pipeline; the web app exposes the agent; the pipeline can be invoked directly.

---

## Current architecture

```
┌────────────────────────────────────────────────────────────────────────────┐
│  Browser (frontend/)                                                       │
│  Single-page app: Process · Analyze · Extract · Summarize · Chat           │
│  SSE streaming for chat · markdown rendering · toast notifications         │
└──────────────────────────────────┬─────────────────────────────────────────┘
                                   │  HTTPS (JSON + SSE)
                                   ▼
┌────────────────────────────────────────────────────────────────────────────┐
│  FastAPI server (server.py)                                                │
│  ┌──────────┬──────────┬───────────┬──────────┬──────────┬──────────────┐  │
│  │ /analyze │ /extract │/summarize │ /process │/pipeline │ /chat (SSE)  │  │
│  └──────────┴──────────┴───────────┴──────────┴──────────┴──────────────┘  │
│  Pydantic request validation · CORS · static file serving (frontend/)      │
└────────────────┬───────────────────────────────────────────┬───────────────┘
                 │ Python function calls                     │ subprocess
                 ▼                                           ▼
┌─────────────────────────────────────┐  ┌───────────────────────────────────┐
│  Agent core (agent/)                │  │  Automation pipeline              │
│  ┌────────────┐  ┌────────────────┐ │  │  (automation/src/)                │
│  │ ReAct loop │  │ Tool router    │ │  │  ┌─────────────────────────────┐  │
│  │ (agent.py) │──│ & dispatcher   │ │  │  │ Connectors (API / file)     │  │
│  └────────────┘  └───────┬────────┘ │  │  └──────────────┬──────────────┘  │
│                          │          │  │                 ▼                 │
│  ┌─────────┬─────────┬───┴────────┐ │  │  ┌─────────────────────────────┐  │
│  │ analyze │ extract │ summarize  │ │  │  │ Transforms:                 │  │
│  └─────────┴─────────┴────────────┘ │  │  │ clean · filter · map        │  │
│  ┌────────────────────────────────┐ │  │  │ aggregate · format          │  │
│  │ run_pipeline (invokes TS)      │─┼──┼─▶└──────────────┬──────────────┘  │
│  └────────────────────────────────┘ │  │                 ▼                 │
│                                     │  │  ┌─────────────────────────────┐  │
│  Claude Sonnet 4 via Anthropic SDK  │  │  │ Output (Markdown / CSV)     │  │
└─────────────────────────────────────┘  │  └─────────────────────────────┘  │
                                         │  Validated with Zod at every step │
                                         └───────────────────────────────────┘
```

---

## Component details

### AI Agent (Python)

The agent implements the **ReAct** (Reasoning + Acting) pattern: it alternates
between thinking about the task and calling tools, synthesising the results into
a final answer.

```
 ┌──────────┐   ┌──────────┐   ┌──────────┐
 │  Think   │──▶│   Act    │──▶│ Observe  │
 └──────────┘   └──────────┘   └─────┬────┘
      ▲                              │
      └──────────────────────────────┘
              (until final answer)
```

Per iteration:

1. The current conversation (system prompt + user task + prior tool results) is sent to Claude.
2. Claude returns either a `tool_use` block or a final text answer.
3. If `tool_use`: the tool runs, the result is appended to the conversation, loop continues.
4. If text: the answer is returned.

**Streaming:** `Agent.run_stream()` uses the Anthropic streaming API and yields text
chunks as they arrive. Tool calls still execute synchronously between segments.

### Tools

Each tool is a Python function with metadata: name, description, JSON Schema.
The agent *does not* hardcode tool logic — it selects tools based on descriptions
at runtime. This is the essence of tool calling.

| Tool             | Purpose                                           | Input                   | Output                   |
|------------------|---------------------------------------------------|-------------------------|--------------------------|
| `analyze_document` | Detect type, extract entities, structure         | text + focus            | structured analysis      |
| `extract_data`    | Pull key-value pairs, tables, lists              | text + fields + strategy| extracted values         |
| `summarize`       | AI-powered (Claude) or extractive summarization  | text + format           | summary                  |
| `run_pipeline`    | Trigger TypeScript automation pipeline           | task + pipeline name    | pipeline output          |

### Automation Pipeline (TypeScript)

A **pipe-and-filter** pipeline. Each step consumes the previous step's output.
Type safety is enforced at every boundary using Zod schemas.

```
 Fetch  →  Clean  →  Filter  →  Map  →  Aggregate  →  Format
```

Two concrete pipelines:

- `posts` — fetches user activity from JSONPlaceholder, aggregates by user.
- `github` — fetches live repos from GitHub API, groups by language, counts stars.

### Web Layer (FastAPI + frontend)

FastAPI serves:

- REST endpoints for each tool, validated with Pydantic models.
- A Server-Sent Events stream for the chat endpoint (`/api/chat`).
- The static frontend (`frontend/index.html`, `app.js`, `style.css`, `examples.js`).
- An auto-generated OpenAPI schema (`/openapi.json`).

The frontend is deliberately **build-step-free** — plain HTML/CSS/JS, no bundler,
no framework. This keeps the deployment footprint tiny and the code readable at
a glance. It will stay that way until a frontend concern actually justifies
tooling (e.g. the Prompt Workbench in Fase 4 might introduce a lightweight setup).

### Integration points

| From              | To                | Mechanism                       |
|-------------------|-------------------|---------------------------------|
| Browser           | FastAPI           | `fetch()` + SSE                 |
| FastAPI           | Agent core        | Direct Python function calls    |
| Agent core        | Tools             | In-process dispatch             |
| Agent core        | TypeScript pipeline | `subprocess` → `npx tsx`     |
| Agent core        | Claude API        | Anthropic SDK (HTTPS)           |

---

## Design decisions

For *why* behind each choice, see [ADRs](./adr/README.md).
Summarised here:

| Decision                        | Rationale                                           | ADR    |
|---------------------------------|-----------------------------------------------------|--------|
| Python for agent                | Best Claude SDK, rich AI/ML ecosystem               | —      |
| TypeScript for pipeline         | Type safety for data flow, Node async model         | —      |
| Tool-based architecture         | Extensible — new capabilities added without changing agent logic | — |
| Zod validation                  | Runtime safety for external data, self-documenting  | —      |
| SQLite (dev) + Postgres (prod)  | Zero-friction local + production-grade deployed     | [001](./adr/001-persistence-strategy.md) |
| Learning notes outside repo     | Professional signal separated from personal study   | [002](./adr/002-learning-docs-outside-repo.md) |

---

## Where we are going

The current architecture (shown above) is **pre-persistence**. All state is in-memory
and lost on process restart. The upgrade plan (Fase 1–9) will evolve the system toward
the target architecture below.

### Target architecture (after Fase 8)

```
┌────────────────────────────────────────────────────────────────────────────┐
│  Browser                                                                   │
│  + Prompt Workbench · Run history · Drag-and-drop upload · Dashboards      │
└──────────────────────────────────┬─────────────────────────────────────────┘
                                   │  HTTPS + CSRF + session cookie + rate-limit
                                   ▼
┌────────────────────────────────────────────────────────────────────────────┐
│  FastAPI (app/)                                                            │
│  Routers: /api/v1/{auth, runs, prompts, upload, chat, process, metrics}    │
│  Middleware: auth · rate-limit · request-id · security headers · CORS      │
│  Observability: structured JSON logs · /metrics (Prometheus)               │
└──────┬─────────────────────────┬──────────────────────────┬────────────────┘
       │                         │                          │
       ▼                         ▼                          ▼
┌──────────────────┐  ┌──────────────────────┐  ┌────────────────────────────┐
│ Agent core       │  │ Persistence layer    │  │ External integrations      │
│ + file parsing   │  │ SQLAlchemy + Alembic │  │  ┌──────────────────────┐  │
│ + prompt cache   │  │ ┌────────┬─────────┐ │  │  │ MCP server           │  │
│ + cost tracking  │  │ │ SQLite │Postgres │ │  │  │ (Claude Desktop)     │  │
│                  │  │ │ (dev)  │ (prod)  │ │  │  └──────────────────────┘  │
│                  │  │ └────────┴─────────┘ │  │  ┌──────────────────────┐  │
│                  │  │                      │  │  │ Copilot Studio       │  │
│                  │  │ Tables:              │  │  │ (OpenAPI manifest)   │  │
│                  │  │  users · runs        │  │  └──────────────────────┘  │
│                  │  │  documents · prompts │  │  ┌──────────────────────┐  │
│                  │  │  prompt_versions     │  │  │ Generic OpenAPI      │  │
│                  │  │  audit_log           │  │  │ (any HTTP client)    │  │
└──────────────────┘  └──────────────────────┘  │  └──────────────────────┘  │
                                                └────────────────────────────┘
```

---

## Further reading

- [ADR index](./adr/README.md) — decisions and tradeoffs
- [SECURITY.md](../SECURITY.md) — threat model and disclosure policy
- [CONTRIBUTING.md](../CONTRIBUTING.md) — development workflow
