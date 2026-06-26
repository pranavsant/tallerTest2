"""
Shared FastAPI dependency providers.

Centralises the most common ``Depends(...)`` targets so that routers import
from one stable location rather than directly from infrastructure modules.

Example usage in a router::

    from fastapi import Depends
    from sqlalchemy.ext.asyncio import AsyncSession
    from src.interfaces.api.core.dependencies import get_db_session

    @router.get("/example")
    async def example(db: AsyncSession = Depends(get_db_session)) -> ...:
        ...
"""
from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.db import get_db


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Thin re-export of ``src.infrastructure.db.get_db``.

    Routers should import ``get_db_session`` from this module so they stay
    decoupled from the infrastructure layer's internal path.
    """
    async for session in get_db():
        yield session
