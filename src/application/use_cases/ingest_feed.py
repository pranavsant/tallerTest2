"""
IngestFeedUseCase

Polls a single feed once and runs the full ingestion pipeline:

    fetch → normalise → deduplicate → store (status=pending) → queue for AI

The use case owns *orchestration only*; the business rules live in the domain
entities (``Feed`` records success/failure and backoff; ``RawFeedItem`` derives
its dedup hash and protects its invariants). I/O is delegated to ports
(``IFeedFetcher``, ``IFeedItemQueue``) and the repositories.

Failure handling (acceptance criterion 5): any error raised while fetching is
caught, recorded on the feed (which advances its exponential-backoff counter),
and persisted. The use case never raises for a fetch failure — it returns an
``IngestFeedResultDTO`` describing the outcome so the scheduler can keep
running other feeds.
"""
from __future__ import annotations

import logging

from src.application.dtos.ingestion_dtos import FetchedItemDTO, IngestFeedResultDTO
from src.application.ports.feed_fetcher import IFeedFetcher
from src.application.ports.feed_item_queue import IFeedItemQueue
from src.domain.entities.feed import Feed
from src.domain.entities.raw_feed_item import RawFeedItem
from src.domain.repositories.feed_repository import IFeedRepository
from src.domain.repositories.raw_feed_item_repository import IRawFeedItemRepository

logger = logging.getLogger(__name__)


class IngestFeedUseCase:
    """Run one ingestion pass over a single feed."""

    def __init__(
        self,
        *,
        feed_repository: IFeedRepository,
        item_repository: IRawFeedItemRepository,
        fetchers: list[IFeedFetcher],
        queue: IFeedItemQueue,
    ) -> None:
        self._feeds = feed_repository
        self._items = item_repository
        self._fetchers = fetchers
        self._queue = queue

    async def execute(self, feed: Feed) -> IngestFeedResultDTO:
        fetcher = self._select_fetcher(feed)
        if fetcher is None:
            error = f"No fetcher available for feed source type '{feed.source_type.value}'"
            logger.warning("%s (feed=%s)", error, feed.id)
            feed.record_ingestion_failure(error)
            await self._feeds.save(feed)
            return IngestFeedResultDTO(
                feed_id=feed.id,
                fetched=0,
                new_items=0,
                duplicates=0,
                succeeded=False,
                error=error,
            )

        try:
            fetched = await fetcher.fetch(feed)
        except Exception as exc:  # noqa: BLE001 — translate any transport error
            error = f"Fetch failed: {exc}"
            logger.warning("Feed %s ingestion failed: %s", feed.id, exc)
            feed.record_ingestion_failure(error)
            await self._feeds.save(feed)
            return IngestFeedResultDTO(
                feed_id=feed.id,
                fetched=0,
                new_items=0,
                duplicates=0,
                succeeded=False,
                error=error,
            )

        new_items = 0
        duplicates = 0
        for fetched_item in fetched:
            item = self._normalise(feed.id, fetched_item)
            if item is None:
                continue
            if await self._items.add_if_new(item):
                new_items += 1
                await self._queue.enqueue(item)
            else:
                duplicates += 1

        feed.record_ingestion_success()
        await self._feeds.save(feed)

        logger.info(
            "Feed %s ingested: %d fetched, %d new, %d duplicate",
            feed.id,
            len(fetched),
            new_items,
            duplicates,
        )
        return IngestFeedResultDTO(
            feed_id=feed.id,
            fetched=len(fetched),
            new_items=new_items,
            duplicates=duplicates,
            succeeded=True,
        )

    # ── Internals ───────────────────────────────────────────────────────────

    def _select_fetcher(self, feed: Feed) -> IFeedFetcher | None:
        for fetcher in self._fetchers:
            if fetcher.supports(feed):
                return fetcher
        return None

    @staticmethod
    def _normalise(feed_id: str, fetched: FetchedItemDTO) -> RawFeedItem | None:
        """Turn a fetched payload into a normalised, hashed RawFeedItem.

        Items carrying no textual signal (neither title nor content) are
        dropped — they cannot be analysed — rather than raising.
        """
        if not (fetched.title or fetched.content):
            return None

        content_hash = RawFeedItem.compute_content_hash(
            feed_id,
            external_id=fetched.external_id,
            title=fetched.title,
            content=fetched.content,
            url=fetched.url,
        )
        return RawFeedItem(
            feed_id=feed_id,
            content_hash=content_hash,
            title=fetched.title,
            content=fetched.content,
            url=fetched.url,
            external_id=fetched.external_id,
            published_at=fetched.published_at,
            raw=fetched.raw,
        )
