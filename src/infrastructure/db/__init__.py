"""
Infrastructure — database package.

Exposes:
  - ``make_engine``         — create an async SQLAlchemy engine from Settings
  - ``make_session_factory`` — create an ``async_sessionmaker`` bound to an engine
  - ``get_session``         — async context manager for use as a FastAPI dependency
"""
from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.infrastructure.config import get_settings


def make_engine() -> AsyncEngine:
    """Create an async SQLAlchemy engine using the configured DATABASE_URL."""
    settings = get_settings()
    return create_async_engine(
        settings.database_url,
        echo=False,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10,
    )


def make_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    """Create a session factory bound to the given engine."""
    return async_sessionmaker(engine, expire_on_commit=False)


# ── Module-level singletons (initialised lazily on first import) ──────────────
_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def _get_session_factory() -> async_sessionmaker[AsyncSession]:
    global _engine, _session_factory
    if _session_factory is None:
        _engine = make_engine()
        _session_factory = make_session_factory(_engine)
    return _session_factory


@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Async context manager that yields a database session.

    Usage as a FastAPI dependency::

        async def my_endpoint(session: AsyncSession = Depends(get_session)):
            ...

    Usage as a plain context manager::

        async with get_session() as session:
            result = await session.execute(...)
    """
    factory = _get_session_factory()
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
