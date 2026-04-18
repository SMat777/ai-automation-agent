# ADR 001: Persistence — SQLite (dev) + Postgres (prod) via SQLAlchemy

- **Status:** Accepted
- **Date:** 2026-04-18
- **Deciders:** Simon Mathiasen

## Context

The application previously held no state — every request was stateless and results
were discarded when the browser closed. To become a useful showcase (and a real
product), we need to persist:

- Documents uploaded and processed
- Run history per user (which tool was called, with what input, what came out)
- Prompt versions for the upcoming Prompt Engineering Workbench
- An audit log for governance

Two competing requirements:

1. **Low friction for first-time users.** A recruiter or developer cloning the repo
   should be able to run the app with `uvicorn app.main:app` — no Docker, no database
   server, no setup. The deployed URL must also just work on first click.

2. **Production-grade durability.** The deployed instance on Fly.io needs concurrent
   connections, point-in-time recovery, and proper ACID guarantees — i.e. a real
   RDBMS.

These are normally satisfied by two different databases. We want both.

## Decision

Use **SQLAlchemy 2.0** as a database abstraction layer. The engine is selected at
runtime from the `DATABASE_URL` environment variable:

- If `DATABASE_URL` is unset or starts with `sqlite://` → use SQLite (file-based, zero ops).
- If `DATABASE_URL` starts with `postgresql://` → use Postgres (connection pool, async driver).

Schema migrations are managed by **Alembic**. The same migration files target both databases.

Default development experience:
```bash
git clone …
pip install -e .
uvicorn app.main:app   # uses ./app.db (SQLite) automatically
```

Production on Fly.io:
```bash
flyctl postgres create
flyctl postgres attach  # sets DATABASE_URL
flyctl deploy
```

## Consequences

### Positive
- **Zero-friction demo.** A new contributor or a recruiter reviewing the repo can run
  the app in under a minute.
- **Dev/prod parity where it matters.** The *code* is identical in both environments;
  only the database URL differs.
- **Learning value.** Working with both databases teaches portable SQL, migration discipline,
  and 12-factor configuration — useful skills regardless of project.
- **Deployment flexibility.** The app can be deployed anywhere that provides a Postgres
  URL: Fly, Railway, Render, AWS RDS, Supabase.

### Negative
- **Two database dialects to support.** Not every SQL feature is identical between
  SQLite and Postgres (JSONB, array types, advisory locks). We must stick to the
  SQLAlchemy subset that both speak, or use feature detection.
- **Slightly more complex connection management.** Pool sizes, async drivers, and
  connection strings differ between the two.

### Neutral
- Tests use SQLite in-memory by default, which is fast but may miss Postgres-specific bugs.
  We address this by running a weekly CI job against a real Postgres container.

## Alternatives considered

- **Postgres only, always via Docker Compose.** Rejected because it requires every
  visitor to have Docker installed and working before they can even run the app.
  Friction kills demos.
- **SQLite only, everywhere.** Rejected because SQLite's single-writer model does not
  scale to concurrent requests on a production server — and because it would miss
  the learning opportunity of operating a real RDBMS in production.
- **A managed BaaS (Supabase, PlanetScale).** Rejected because it couples the project
  to a specific provider and hides the learning surface we want.

## References

- Upgrade plan: Fase 1 — Persistens
- [SQLAlchemy 2.0 documentation](https://docs.sqlalchemy.org/en/20/)
- [Alembic tutorial](https://alembic.sqlalchemy.org/en/latest/tutorial.html)
- [12-factor app: config](https://12factor.net/config)
