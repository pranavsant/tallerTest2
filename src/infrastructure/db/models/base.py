"""
Declarative base for all SQLAlchemy ORM models.

All models must inherit from ``Base`` so that Alembic autogenerate can
discover them via ``Base.metadata``.
"""
from __future__ import annotations

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Shared declarative base — do not add table columns here."""
