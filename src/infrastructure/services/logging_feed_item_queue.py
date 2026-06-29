"""
LoggingFeedItemQueue

A minimal IFeedItemQueue implementation. Newly-ingested items are already
durably persisted in ``raw_feed_items`` with ``status='pending'`` — that table
*is* the work queue the AI-analysis stage drains. This adapter therefore just
records the handoff so the pipeline has a single, swappable enqueue point.

In a production deployment this would be replaced by an adapter that publishes
to a real broker (e.g. a Postgres ``LISTEN/NOTIFY`` channel, Redis, or SQS)
without touching any other layer.
"""
from __future__ import annotations

import logging

from src.application.ports.feed_item_queue import IFeedItemQueue
from src.domain.entities.raw_feed_item import RawFeedItem

logger = logging.getLogger(__name__)


class LoggingFeedItemQueue(IFeedItemQueue):
    """Records the AI-analysis handoff for each newly-ingested item."""

    async def enqueue(self, item: RawFeedItem) -> None:
        logger.info(
            "Queued raw feed item for AI analysis (item=%s, feed=%s, title=%r)",
            item.id,
            item.feed_id,
            item.title,
        )
