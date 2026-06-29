"""
Unit tests for IngestFeedUseCase — the fetch→normalise→dedup→store→queue pass.

All collaborators are in-memory stubs; no network, no DB, no APScheduler.
"""
from __future__ import annotations

from src.application.dtos.ingestion_dtos import FetchedItemDTO
from src.application.ports.feed_fetcher import IFeedFetcher
from src.application.ports.feed_item_queue import IFeedItemQueue
from src.application.use_cases.ingest_feed import IngestFeedUseCase
from src.domain.entities.feed import Feed
from src.domain.entities.raw_feed_item import RawFeedItem
from src.domain.repositories.feed_repository import IFeedRepository
from src.domain.repositories.raw_feed_item_repository import IRawFeedItemRepository
from src.domain.value_objects.feed_source_type import FeedSourceType
from src.domain.value_objects.feed_status import FeedStatus
from src.domain.value_objects.raw_feed_item_status import RawFeedItemStatus

# ── Stubs ────────────────────────────────────────────────────────────────────


class InMemoryFeedRepository(IFeedRepository):
    def __init__(self) -> None:
        self._store: dict[str, Feed] = {}

    async def save(self, feed: Feed) -> None:
        self._store[feed.id] = feed

    async def get_by_id(self, feed_id: str) -> Feed | None:
        return self._store.get(feed_id)

    async def list_by_status(self, status, *, limit=50, offset=0):  # type: ignore[no-untyped-def]
        return [f for f in self._store.values() if f.status == status]

    async def list_all(self, *, limit=50, offset=0):  # type: ignore[no-untyped-def]
        return list(self._store.values())

    async def delete(self, feed_id: str) -> None:
        self._store.pop(feed_id, None)

    async def exists(self, feed_id: str) -> bool:
        return feed_id in self._store


class InMemoryItemRepository(IRawFeedItemRepository):
    def __init__(self) -> None:
        self.items: dict[str, RawFeedItem] = {}
        self._hashes: set[tuple[str, str]] = set()

    async def add_if_new(self, item: RawFeedItem) -> bool:
        key = (item.feed_id, item.content_hash)
        if key in self._hashes:
            return False
        self._hashes.add(key)
        self.items[item.id] = item
        return True

    async def exists_by_content_hash(self, feed_id: str, content_hash: str) -> bool:
        return (feed_id, content_hash) in self._hashes

    async def get_by_id(self, item_id: str) -> RawFeedItem | None:
        return self.items.get(item_id)

    async def list_by_status(self, status, *, limit=100, offset=0):  # type: ignore[no-untyped-def]
        return [i for i in self.items.values() if i.status == status]

    async def save(self, item: RawFeedItem) -> None:
        self.items[item.id] = item


class StubFetcher(IFeedFetcher):
    def __init__(self, items: list[FetchedItemDTO] | None = None, *, raises: bool = False) -> None:
        self._items = items or []
        self._raises = raises

    def supports(self, feed: Feed) -> bool:
        return True

    async def fetch(self, feed: Feed) -> list[FetchedItemDTO]:
        if self._raises:
            raise RuntimeError("upstream down")
        return self._items


class RecordingQueue(IFeedItemQueue):
    def __init__(self) -> None:
        self.enqueued: list[RawFeedItem] = []

    async def enqueue(self, item: RawFeedItem) -> None:
        self.enqueued.append(item)


# ── Fixtures ──────────────────────────────────────────────────────────────────


def _feed() -> Feed:
    return Feed(
        name="Poller",
        source_type=FeedSourceType.POLLING,
        endpoint_url="https://example.com/rss",
        polling_interval_seconds=60,
    )


def _build(fetcher: IFeedFetcher):  # type: ignore[no-untyped-def]
    feeds = InMemoryFeedRepository()
    items = InMemoryItemRepository()
    queue = RecordingQueue()
    use_case = IngestFeedUseCase(
        feed_repository=feeds,
        item_repository=items,
        fetchers=[fetcher],
        queue=queue,
    )
    return use_case, feeds, items, queue


# ── Tests ─────────────────────────────────────────────────────────────────────


class TestHappyPath:
    async def test_stores_and_queues_new_items(self) -> None:
        fetched = [
            FetchedItemDTO(title="One", external_id="a"),
            FetchedItemDTO(title="Two", external_id="b"),
        ]
        use_case, feeds, items, queue = _build(StubFetcher(fetched))
        feed = _feed()

        result = await use_case.execute(feed)

        assert result.succeeded
        assert result.fetched == 2
        assert result.new_items == 2
        assert result.duplicates == 0
        assert len(items.items) == 2
        assert len(queue.enqueued) == 2
        # Stored items start pending.
        assert all(i.status == RawFeedItemStatus.PENDING for i in items.items.values())
        # Feed marked successful and persisted.
        assert (await feeds.get_by_id(feed.id)).consecutive_failures == 0  # type: ignore[union-attr]

    async def test_deduplicates_across_polls(self) -> None:
        fetched = [FetchedItemDTO(title="Dupe", external_id="same")]
        use_case, _feeds, items, queue = _build(StubFetcher(fetched))
        feed = _feed()

        first = await use_case.execute(feed)
        second = await use_case.execute(feed)

        assert first.new_items == 1
        assert second.new_items == 0
        assert second.duplicates == 1
        assert len(items.items) == 1
        assert len(queue.enqueued) == 1  # only the novel item was queued

    async def test_drops_items_with_no_text(self) -> None:
        fetched = [
            FetchedItemDTO(title=None, content=None, external_id="empty"),
            FetchedItemDTO(title="Real", external_id="real"),
        ]
        use_case, _feeds, items, _queue = _build(StubFetcher(fetched))

        result = await use_case.execute(_feed())

        assert result.new_items == 1
        assert len(items.items) == 1


class TestFailureHandling:
    async def test_fetch_error_records_failure_and_does_not_raise(self) -> None:
        use_case, feeds, items, queue = _build(StubFetcher(raises=True))
        feed = _feed()

        result = await use_case.execute(feed)

        assert result.succeeded is False
        assert result.error is not None and "upstream down" in result.error
        assert len(items.items) == 0
        assert len(queue.enqueued) == 0
        stored = await feeds.get_by_id(feed.id)
        assert stored is not None
        assert stored.status == FeedStatus.ERROR
        assert stored.consecutive_failures == 1

    async def test_no_fetcher_records_failure(self) -> None:
        class NoMatch(StubFetcher):
            def supports(self, feed: Feed) -> bool:
                return False

        use_case, feeds, _items, _queue = _build(NoMatch())
        feed = _feed()

        result = await use_case.execute(feed)

        assert result.succeeded is False
        assert "No fetcher" in (result.error or "")
        assert (await feeds.get_by_id(feed.id)).consecutive_failures == 1  # type: ignore[union-attr]
