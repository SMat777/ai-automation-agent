"""Alembic environment configuration.

Wires Alembic into the application:
  - pulls the database URL from our Settings (not from alembic.ini)
  - imports all ORM models so that --autogenerate sees them
  - exposes Base.metadata as the target schema

Run migrations with:
    alembic upgrade head       # apply all pending
    alembic revision --autogenerate -m "short description"
    alembic downgrade -1       # revert one step
"""

from __future__ import annotations

import sys
from logging.config import fileConfig
from pathlib import Path

from sqlalchemy import engine_from_config, pool

from alembic import context

# Make the project root importable so we can reach app.*
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.config import get_settings  # noqa: E402
from app.db.base import Base  # noqa: E402
from app import models  # noqa: F401, E402  — registers models on Base.metadata

# Alembic config object — gives access to values in alembic.ini.
config = context.config

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Override the URL from alembic.ini with our runtime-configured URL,
# so `alembic upgrade` targets the same DB the app will use.
config.set_main_option("sqlalchemy.url", get_settings().database_url)

# Metadata that --autogenerate diffs against.
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    Emits SQL to stdout without connecting to a database. Useful for
    reviewing what a migration would do before running it.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        # SQLite does not support ALTER TABLE for many operations;
        # render_as_batch enables Alembic's batch mode which works around it.
        render_as_batch=url.startswith("sqlite"),
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode — connects to the DB and applies them."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        is_sqlite = connection.dialect.name == "sqlite"
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=is_sqlite,  # SQLite-friendly ALTER TABLE
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
