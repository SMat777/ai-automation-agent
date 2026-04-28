# Architecture Decision Records (ADRs)

This directory contains records of significant architectural decisions made in
the ai-automation-agent project.

## Why ADRs?

When someone joins the project (or revisits it months later) and asks
*"Why did we do X this way?"* — the answer is here. ADRs prevent rehashing
the same design discussions and document the context that shaped each decision.

## Format

Each ADR follows a lightweight version of the [Nygard ADR format](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions):

1. **Title** — short, descriptive
2. **Status** — Proposed, Accepted, Deprecated, Superseded
3. **Context** — What forces are at play? What problem are we solving?
4. **Decision** — What did we decide?
5. **Consequences** — What are the tradeoffs? What are we now committed to?

## Index

| # | Title | Status |
|---|-------|--------|
| [001](./001-persistence-strategy.md) | Persistence: SQLite (dev) + Postgres (prod) via SQLAlchemy | Accepted |
| [002](./002-learning-docs-outside-repo.md) | Personal learning notes live outside the repo | Accepted |
| [003](./003-orm-and-migrations.md) | ORM and migrations: SQLAlchemy 2.0 + Alembic | Accepted |
| [004](./004-frontend-as-product.md) | Frontend is the product, not a demo shell | Accepted |
| [005](./005-explicit-run-logging.md) | Explicit run logging over implicit middleware | Accepted |

## Writing a new ADR

1. Copy `template.md` to `NNN-short-title.md` (next available number).
2. Fill in all sections — context first, then decision, then consequences.
3. Keep it short: 1-2 pages max. If it's longer, the decision is probably too big.
4. Add it to the index above.
5. Commit with message `docs: add ADR NNN - <title>`.

Once an ADR is merged to `main`, it is **immutable** except for status changes.
If the decision changes later, write a new ADR that supersedes the old one.
