"""SQLAlchemy declarative base.

All ORM models inherit from ``Base``. Kept in its own module so that Alembic
can import it without pulling in the entire database engine on module load
(which would matter once we add async engines).
"""

from __future__ import annotations

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Declarative base for all ORM models in the project.

    Using ``DeclarativeBase`` (SQLAlchemy 2.0 style) gives us typed ``Mapped[...]``
    attributes that integrate with mypy and IDE autocomplete — see ADR 003.
    """
