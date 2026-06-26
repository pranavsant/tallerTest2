"""
Alembic environment — async SQLAlchemy setup.

Supports both offline (SQL dump) and online (live DB) migration modes.
The DATABASE_URL is read from the project Settings so it stays in sync
with the rest of the application.
"""
from __future__ import annotations

import asyncio
import os
import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

# ── Make src importable when running `alembic` from project root ─────────────
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# ── Import ORM metadata so Alembic can detect autogenerate changes ────────────
# The side-effect import of `src.infrastructure.db.models` registers all
# ORM model classes against Base.metadata.
from src.infrastructure.db.models.base import Base  # noqa: E402
import src.infrastructure.db.models as _models  # noqa: E402, F401

# ── Alembic Config object (gives access to values in alembic.ini) ─────────────
config = context.config

# ── Override sqlalchemy.url from environment (takes precedence over .ini) ─────
_db_url = os.environ.get("DATABASE_URL", "")
if _db_url:
    # Ensure we use the asyncpg driver scheme
    _db_url = _db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    config.set_main_option("sqlalchemy.url", _db_url)

# ── Logging ───────────────────────────────────────────────────────────────────
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# ── Target metadata (used for autogenerate) ───────────────────────────────────
target_metadata = Base.metadata


# ── Offline mode ─────────────────────────────────────────────────────────────
def run_migrations_offline() -> None:
    """
    Run migrations without a live DB connection.

    Emits SQL to stdout/file, which can be reviewed and applied manually.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


# ── Online mode ───────────────────────────────────────────────────────────────
def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Create an async engine and run migrations through a sync connection."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Entry point for online migration mode."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
