"""
IRawFeedItemRepository — domain interface for RawFeedItem persistence.

Implementations live in infrastructure/; this file contains zero I/O.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from src.domain.entities.raw_feed_item import RawFeedItem
from src.domain.value_objects.raw_feed_item_status import RawFeedItemStatus


class IRawFeedItemRepository(ABC):
    """Abstract repository contract for RawFeedItem persistence."""

    @abstractmethod
    async def add_if_new(self, item: RawFeedItem) -> bool:
        """Persist *item* unless one with the same content hash already exists.

        Returns ``True`` if the item was newly stored, ``False`` if it was a
        duplicate and therefore skipped. Implementations must make the
        check-and-insert atomic (e.g. via a unique constraint) so concurrent
        polls cannot both insert the same item.
        """
        ...

    @abstractmethod
    async def exists_by_content_hash(self, feed_id: str, content_hash: str) -> bool:
        """Return True if an item with this content hash already exists."""
        ...

    @abstractmethod
    async def get_by_id(self, item_id: str) -> RawFeedItem | None:
        """Return a RawFeedItem by its ID, or None if not found."""
        ...

    @abstractmethod
    async def list_by_status(
        self,
        status: RawFeedItemStatus,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> list[RawFeedItem]:
        """Return paginated items filtered by pipeline status."""
        ...

    @abstractmethod
    async def save(self, item: RawFeedItem) -> None:
        """Persist status/error changes to an existing item."""
        ...
