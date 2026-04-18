# ADR 002: Personal learning notes live outside the repo

- **Status:** Accepted
- **Date:** 2026-04-18
- **Deciders:** Simon Mathiasen

## Context

This project serves two audiences:

1. **External readers** — potential employers, other developers, maintainers.
   They expect professional documentation: architecture, decisions, runbook, security.
2. **The author** — who is using the project to learn full-stack development,
   persistence, security, and operations. This learning produces notes, cheatsheets,
   tjek-dig-selv questions, and retrospectives.

Mixing both in a single `docs/` directory risks:

- Diluting professional signal (a repo full of "how I learned what a primary key is"
  suggests inexperience, not growth).
- Fragmenting audiences who only want one of the two.
- Making it harder for the author to iterate on personal notes without polluting
  commit history.

## Decision

Split documentation into two tracks:

### In the repo (`ai-automation-agent/docs/`)
- `ARCHITECTURE.md` — system overview, diagrams
- `adr/` — Architecture Decision Records
- `SECURITY.md` — threat model, disclosure policy
- `RUNBOOK.md` — operational procedures (incident response)
- `INTEGRATIONS.md` — MCP, Copilot Studio, generic OpenAPI
- `CASE-STUDY.md` — project narrative for portfolio use

### Outside the repo (`~/Developer/ai-automation-agent-notes/`)
- `guides/` — per-phase learning documents (concepts, analogies, faldgruber)
- `retros/` — personal retrospectives per phase
- `cheatsheets/` — quick-reference for recurring operations

The notes directory is **not** git-tracked and may be managed separately
(Obsidian sync, iCloud backup, or deletion if it becomes outdated).

## Consequences

### Positive
- **Clear professional signal.** The repo reads as a mature project to external reviewers.
- **Author retains detailed learning record.** Nothing is lost — it just lives in a
  location aligned with its audience.
- **Independent iteration.** Notes can be messy, rewritten, or discarded without
  polluting commit history.

### Negative
- **Two locations to maintain.** The author must remember to update both when
  a concept or decision crosses boundaries.
- **Notes are not backed up by git.** Author is responsible for backup strategy
  (iCloud, Obsidian sync, periodic snapshots).

### Neutral
- Notes and repo-docs may occasionally reference each other. Cross-linking is done
  with absolute paths (not git-relative).

## Alternatives considered

- **Keep everything in the repo.** Rejected — see context, signal-to-noise problem.
- **Keep notes in a `docs/learning/` subdirectory in the repo and `.gitignore` it.**
  Rejected because an ignored directory in the repo is confusing (visible in `ls`
  but invisible in git status) and creates a weird split between tracked and
  untracked files.
- **Host notes in a separate public repo.** Rejected for now because notes are
  intentionally personal and informal. Revisit if polished learning content emerges.

## References

- Upgrade plan: Fase 0 — Landing zone
- Personal notes location: `~/Developer/ai-automation-agent-notes/`
