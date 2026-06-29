"""
IFeedItemQueue — application port for handing normalised items off for
downstream AI analysis.

Implemented in infrastructure. The ingestion pipeline does not care whether
the queue is an in-process task queue, a database-backed work table, or an
external broker — it only enqueues newly-ingested items for later analysis.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from src.domain.entities.raw_feed_item import RawFeedItem


class IFeedItemQueue(ABC):
    """Abstraction over the queue that feeds the AI-analysis stage."""

    @abstractmethod
    async def enqueue(self, item: RawFeedItem) -> None:
        """Submit a newly-ingested item for AI analysis."""
        ...
