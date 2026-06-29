"""
IFeedRepository — domain interface for Feed persistence.

Implementations live in infrastructure/; this file contains zero I/O.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from src.domain.entities.feed import Feed
from src.domain.value_objects.feed_status import FeedStatus


class IFeedRepository(ABC):
    """Abstract repository contract for Feed persistence."""

    @abstractmethod
    async def save(self, feed: Feed) -> None:
        """Persist a new or updated Feed."""
        ...

    @abstractmethod
    async def get_by_id(self, feed_id: str) -> Feed | None:
        """Return a Feed by its ID, or None if not found."""
        ...

    @abstractmethod
    async def list_by_status(
        self,
        status: FeedStatus,
        *,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Feed]:
        """Return paginated feeds filtered by status."""
        ...

    @abstractmethod
    async def list_all(
        self,
        *,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Feed]:
        """Return all feeds (paginated)."""
        ...

    @abstractmethod
    async def delete(self, feed_id: str) -> None:
        """Hard-delete a Feed by ID."""
        ...

    @abstractmethod
    async def exists(self, feed_id: str) -> bool:
        """Return True if a Feed with the given ID exists."""
        ...
