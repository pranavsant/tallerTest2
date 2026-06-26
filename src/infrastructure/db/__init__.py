"""
Async database pool — SQLAlchemy 2.x + asyncpg.

Lifecycle
---------
Call ``init_db()`` once on application startup and ``close_db()`` on shutdown.
Both are wired into the FastAPI lifespan context in ``src/interfaces/api/main.py``.

Session dependency
------------------
Use ``get_db`` as a FastAPI ``Depends`` to get a scoped ``AsyncSession``:

    async def my_handler(db: AsyncSession = Depends(get_db)) -> ...:
        ...

The session is committed on clean exit and rolled back on exception.
"""
from __future__ import annotations

import logging
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.infrastructure.config import get_settings

logger = logging.getLogger(__name__)

# ── Module-level singletons (initialised by init_db / cleared by close_db) ───

_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


# ── Public lifecycle API ───────────────────────────────────────────────────────


def make_engine() -> AsyncEngine:
    """Create (but do not store) an async engine from current settings."""
    settings = get_settings()
    return create_async_engine(
        settings.database_url,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10,
        echo=not settings.is_production,
        future=True,
    )


def make_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    """Create (but do not store) a session factory bound to *engine*."""
    return async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
        autocommit=False,
    )


async def init_db() -> None:
    """
    Initialise the module-level engine and session factory.

    Safe to call more than once — subsequent calls are no-ops.
    Logs a warning (not an exception) when ``DATABASE_URL`` is unreachable so
    the application can still start in environments without a live DB.
    """
    global _engine, _session_factory

    if _engine is not None:
        return  # already initialised

    try:
        engine = make_engine()
        # Verify connectivity by borrowing a connection from the pool.
        async with engine.connect() as conn:
            await conn.exec_driver_sql("SELECT 1")

        _engine = engine
        _session_factory = make_session_factory(engine)
        logger.info("Database pool initialised (pool_size=5, max_overflow=10)")
    except Exception as exc:  # pragma: no cover
        logger.warning(
            "Database pool could not be initialised: %s — continuing without DB.",
            exc,
        )


async def close_db() -> None:
    """Dispose of the engine / connection pool on application shutdown."""
    global _engine, _session_factory

    if _engine is not None:
        await _engine.dispose()
        _engine = None
        _session_factory = None
        logger.info("Database pool closed")


# ── FastAPI dependency ─────────────────────────────────────────────────────────


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Yield a scoped ``AsyncSession``.

    Commits automatically on success; rolls back on any exception so that
    partial writes are never persisted.  The session is always closed in the
    ``finally`` block.

    Raises ``RuntimeError`` if the pool has not been initialised (i.e.
    ``init_db()`` was never called).
    """
    if _session_factory is None:
        raise RuntimeError(
            "Database pool is not initialised. "
            "Ensure init_db() is called during application startup."
        )

    async with _session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
