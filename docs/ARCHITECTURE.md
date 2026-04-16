# Architecture

## Overview

This project consists of two main components that work together:

1. **AI Agent** (Python) — An intelligent agent that receives tasks, decides which tools to use, executes them, and synthesizes results
2. **Automation Pipeline** (TypeScript) — A data processing pipeline that orchestrates multi-step workflows

## AI Agent Architecture

### The Agent Loop

The agent follows a **ReAct** (Reasoning + Acting) pattern:

```
User Task → Think → Choose Tool → Execute → Observe → Think → ... → Final Answer
```

Each iteration:
1. The agent receives the current conversation (system prompt + user task + previous tool results)
2. Claude decides whether to call a tool or return a final answer
3. If a tool is called, the result is added to the conversation
4. The loop continues until Claude returns a final text response

### Tool System

Tools are Python functions decorated with metadata that tells the agent what they do:

```python
# Each tool has:
# - name: unique identifier
# - description: what it does (used by the agent to decide when to use it)
# - input_schema: JSON Schema defining expected parameters
# - handler: the actual function that executes
```

The agent doesn't have hardcoded logic for when to use each tool — it decides based on the task description and tool descriptions. This is the core of **tool calling**: the AI model selects and parameterizes tools at runtime.

### Available Tools

| Tool | Purpose | Input | Output |
|------|---------|-------|--------|
| `analyze_document` | Extract structure and key points from text | Document text | Structured analysis |
| `extract_data` | Pull specific data points from structured text | Text + schema | Extracted data |
| `summarize` | Create concise summaries | Text + format | Summary |

### Prompt Engineering

System prompts are stored in `agent/prompts/` and define:
- The agent's role and capabilities
- Available tools and when to use them
- Output format expectations
- Error handling behavior

## Automation Pipeline Architecture

### Pipeline Pattern

The TypeScript automation follows a **pipe-and-filter** pattern:

```
Source → Connector → Transform → Transform → Output
```

Each step:
1. **Connectors** fetch data from external sources (APIs, files)
2. **Transforms** clean, map, and restructure data
3. **Output** delivers results (files, reports, notifications)

### Data Flow

```typescript
// Conceptual pipeline
const result = await pipeline([
  fetchFromAPI("https://api.example.com/data"),
  cleanData({ removeNulls: true }),
  mapToSchema(outputSchema),
  writeReport("output/report.json")
]);
```

### Type Safety

All data flowing through the pipeline is validated with **Zod** schemas:
- Input validation at connectors
- Transform type guarantees
- Output schema enforcement

## Integration Layer

The agent and pipeline communicate through:

1. **Agent → Pipeline**: Agent calls a tool that triggers a pipeline run
2. **Pipeline → Agent**: Pipeline output is fed back as tool results

This creates a feedback loop where the agent can orchestrate complex multi-step processes that combine AI reasoning with deterministic data processing.

## Design Decisions

| Decision | Rationale |
|----------|-----------|
| Python for agent | Best SDK support for Claude API, rich AI ecosystem |
| TypeScript for automation | Type safety for data pipelines, Node.js async model |
| Separate concerns | Agent handles reasoning, pipeline handles data flow |
| Tool-based architecture | Extensible — add new capabilities without changing agent logic |
| Zod validation | Runtime safety for external data, self-documenting schemas |
