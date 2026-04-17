# Contributing & Development Workflow

This document describes the Git workflow, branching strategy, and quality standards used in this project.

## Branch Strategy

```
main (protected – only merged PRs)
 └── feature/agent-core
 └── feature/automation-pipeline
 └── feature/agent-tools
 └── docs/learning-guides
 └── fix/agent-error-handling
```

**Branch naming convention:**
- `feature/<name>` — New functionality
- `fix/<name>` — Bug fixes
- `docs/<name>` — Documentation changes
- `refactor/<name>` — Code restructuring without behavior changes

## Development Cycle

### 1. Pick an Issue

All work starts with a GitHub issue. Check the [project board](https://github.com/SMat777/ai-automation-agent/projects) for available tasks.

### 2. Create a Branch

```bash
git checkout main
git pull origin main
git checkout -b feature/my-feature
```

### 3. Write Code + Tests

- Python code follows PEP 8 (enforced by ruff)
- TypeScript code follows strict tsconfig
- Every feature needs at least one test
- Update documentation if behavior changes

### 4. Commit with Conventional Messages

```
feat: add document analysis tool
fix: handle empty API response in connector
docs: add AI agents learning guide
test: add agent tool routing tests
refactor: extract prompt templates to separate module
```

Format: `<type>: <short description>`

Types: `feat`, `fix`, `docs`, `test`, `refactor`, `chore`, `ci`

### 5. Push & Create Pull Request

```bash
git push -u origin feature/my-feature
gh pr create --title "feat: add document analysis tool" --body "..."
```

**PR must include:**
- Summary of changes
- Link to related issue(s)
- Test results (screenshot or output)

### 6. CI Must Pass

GitHub Actions runs automatically on every push:
- Python: ruff lint + pytest
- TypeScript: tsc type-check + vitest

### 7. Merge to Main

After CI passes and PR is reviewed, merge via GitHub.

## Code Standards

### Python

- Python 3.11+
- Type hints on all function signatures
- Docstrings on public functions
- Tests in `tests/agent/` using pytest

### TypeScript

- Strict TypeScript config
- Zod for runtime validation of external data
- Tests in `tests/automation/` using vitest

## Issue Labels

| Label | Description |
|-------|-------------|
| `feature` | New functionality |
| `bug` | Something broken |
| `docs` | Documentation |
| `phase-0` to `phase-4` | Development phase |
| `python` | Python agent work |
| `typescript` | TypeScript automation work |
| `good-first-issue` | Good starting point |

## Milestones

| Milestone | Description |
|-----------|-------------|
| Phase 0: Setup | Project structure, CI/CD, docs |
| Phase 1: Agent Core | Python AI agent with tool calling |
| Phase 2: Automation | TypeScript pipeline |
| Phase 3: Integration | Agent + Pipeline working together |
| Phase 4: Polish | Tests, docs, v1.0 release |
