# ADR 003: ORM and migrations — SQLAlchemy 2.0 + Alembic

- **Status:** Accepted
- **Date:** 2026-04-18
- **Deciders:** Simon Mathiasen
- **Depends on:** [ADR 001](./001-persistence-strategy.md)

## Context

[ADR 001](./001-persistence-strategy.md) established that the app will persist data
using SQLite in development and Postgres in production, selected at runtime via
`DATABASE_URL`. That ADR left open *how* the application code interacts with those
databases and how schema evolution is managed.

Two questions need an answer before Fase 1 implementation begins:

1. **How should Python code talk to the database?** Raw SQL strings, a lightweight
   query builder, or a full ORM?
2. **How should schema changes be versioned and deployed?** Manual `ALTER TABLE`
   scripts, Django-style migrations, or a database-agnostic migration tool?

Both decisions need to be compatible with the dual-database strategy from ADR 001
and with the zero-friction dev experience we committed to.

## Decision

### Object-Relational Mapper: SQLAlchemy 2.0

Use SQLAlchemy 2.0 with the typed ORM API (`Mapped[...]` + `mapped_column(...)`),
not the 1.x-style declarative base.

```python
class Run(Base):
    __tablename__ = "runs"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    tool_name: Mapped[str] = mapped_column(String(50), index=True)
    output_json: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
```

### Migration tool: Alembic

Use Alembic with auto-generate enabled but never blindly trusted. Every
auto-generated migration is reviewed by hand before being committed.

Migration workflow:
1. Edit the model (`app/models/*.py`)
2. `alembic revision --autogenerate -m "short description"`
3. Review the generated file in `alembic/versions/`
4. `alembic upgrade head` locally
5. Run tests — they must still pass
6. Commit *both* the model change and the migration in the same commit
7. In production (Fly.io): migration runs automatically as a release-command
   before the new app code starts

## Consequences

### Positive

- **Single source of truth for schema.** Python models drive both the SQL schema
  (via migrations) and the app's object model. No divergence possible.
- **Database portability.** SQLAlchemy abstracts 95% of the difference between
  SQLite and Postgres, satisfying ADR 001's dual-database requirement.
- **SQL-injection protection is free.** Parameterised queries everywhere by default.
- **Type hints integrate with `mypy`.** Model attributes are typed, so IDE
  autocomplete and static analysis work as expected — no opaque `dict`-based APIs.
- **Alembic's migration chain is reviewable in git.** Every schema change is a
  reviewed, commit-sized file — schema history lives alongside code history.

### Negative

- **SQLAlchemy 2.0 has a learning curve.** The new typed API differs from the
  widely-documented 1.x style; some Stack Overflow answers will be misleading.
- **Auto-generated migrations can be wrong.** Alembic cannot detect semantic
  changes (e.g. renaming a column looks like "drop + create" to it). Reviewing
  every generated file is mandatory, not optional.
- **Two databases means two dialects to respect.** We must stick to features
  supported by both SQLite and Postgres, or use dialect-specific code guarded by
  `engine.dialect.name` checks.

### Neutral

- Tests use SQLite in-memory (`sqlite:///:memory:`) for speed. A weekly CI job
  will exercise the migration chain against a real Postgres container to catch
  dialect drift (introduced in Fase 8).

## Alternatives considered

- **Raw SQL via `sqlite3` / `psycopg`.** Rejected: we lose type safety, SQL-injection
  protection by default, and database portability. The time saved in "simplicity"
  is spent many times over in hand-written query code and migration scripts.

- **SQLModel** (FastAPI-friendly wrapper on SQLAlchemy + Pydantic). Considered
  seriously — it reduces boilerplate by unifying ORM models and API schemas. Rejected
  for now because SQLModel is still on SQLAlchemy 1.x internally and the upstream
  story for 2.0 is unstable. We will revisit when SQLModel 2.0 is stable.

- **Tortoise ORM / Peewee / Prisma-Python.** Smaller communities, fewer recipes for
  Postgres-specific features, less enterprise adoption. Rejected on ecosystem grounds.

- **Django-style migrations (without Django).** Alembic covers the same ground
  with less ceremony and integrates natively with SQLAlchemy.

- **No ORM, just SQL files in `migrations/`.** Viable for tiny projects. Rejected
  because Fase 4 (Prompt Workbench) will need fairly complex queries — aggregate
  prompt-run statistics, eval scores, cost per prompt — and writing those as
  portable SQL by hand is significantly more work than using an ORM.

## References

- [ADR 001 — persistence strategy](./001-persistence-strategy.md) (parent decision)
- [SQLAlchemy 2.0 ORM Quickstart](https://docs.sqlalchemy.org/en/20/orm/quickstart.html)
- [Alembic: Auto Generating Migrations](https://alembic.sqlalchemy.org/en/latest/autogenerate.html)
- Learning notes: `~/Developer/ai-automation-agent-notes/guides/01-persistens.md`
