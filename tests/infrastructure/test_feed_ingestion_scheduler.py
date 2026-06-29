"""
Unit tests for FeedIngestionScheduler.

The APScheduler is created but never started, so the asyncio clock never fires;
we drive the sync/poll coroutines directly and assert on the resulting job set.
"""
from __future__ import annotations

from src.application.dtos.ingestion_dtos import IngestFeedResultDTO
from src.domain.entities.feed import Feed
from src.domain.value_objects.feed_source_type import FeedSourceType
from src.domain.value_objects.feed_status import FeedStatus
from src.infrastructure.services.feed_ingestion_scheduler import (
    _FEED_JOB_PREFIX,
    FeedIngestionScheduler,
)


class FakeFeedRepo:
    def __init__(self, feeds: list[Feed]) -> None:
        self._feeds = {f.id: f for f in feeds}

    async def list_by_status(self, status, *, limit=50, offset=0):  # type: ignore[no-untyped-def]
        return [f for f in self._feeds.values() if f.status == status]

    async def get_by_id(self, feed_id):  # type: ignore[no-untyped-def]
        return self._feeds.get(feed_id)

    # Unused interface methods
    async def save(self, feed):  # type: ignore[no-untyped-def]
        self._feeds[feed.id] = feed

    async def list_all(self, *, limit=50, offset=0):  # type: ignore[no-untyped-def]
        return list(self._feeds.values())

    async def delete(self, feed_id):  # type: ignore[no-untyped-def]
        self._feeds.pop(feed_id, None)

    async def exists(self, feed_id):  # type: ignore[no-untyped-def]
        return feed_id in self._feeds

    def remove(self, feed_id: str) -> None:
        self._feeds.pop(feed_id, None)


class FakeIngestUseCase:
    def __init__(self) -> None:
        self.calls: list[str] = []

    async def execute(self, feed: Feed) -> IngestFeedResultDTO:
        self.calls.append(feed.id)
        feed.record_ingestion_success()
        return IngestFeedResultDTO(
            feed_id=feed.id,
            fetched=0,
            new_items=0,
            duplicates=0,
            succeeded=True,
        )


def _polling_feed(name: str = "Poller") -> Feed:
    return Feed(
        name=name,
        source_type=FeedSourceType.POLLING,
        endpoint_url="https://example.com/rss",
        polling_interval_seconds=60,
    )


def _build(feeds: list[Feed]):  # type: ignore[no-untyped-def]
    repo = FakeFeedRepo(feeds)
    use_case = FakeIngestUseCase()
    scheduler = FeedIngestionScheduler(
        feed_repository=repo,  # type: ignore[arg-type]
        ingest_use_case=use_case,  # type: ignore[arg-type]
    )
    return scheduler, repo, use_case


def _feed_job_ids(scheduler: FeedIngestionScheduler) -> set[str]:
    return {
        j.id[len(_FEED_JOB_PREFIX):]
        for j in scheduler._scheduler.get_jobs()
        if j.id.startswith(_FEED_JOB_PREFIX)
    }


class TestSync:
    async def test_schedules_a_job_per_pollable_feed(self) -> None:
        f1, f2 = _polling_feed("A"), _polling_feed("B")
        scheduler, _repo, _uc = _build([f1, f2])

        await scheduler._sync_feeds()

        assert _feed_job_ids(scheduler) == {f1.id, f2.id}

    async def test_ignores_non_polling_and_disabled_feeds(self) -> None:
        webhook = Feed(
            name="Hook",
            source_type=FeedSourceType.WEBHOOK,
            endpoint_url="https://example.com/hook",
        )
        disabled = _polling_feed("Off")
        disabled.disable()
        active = _polling_feed("On")
        scheduler, _repo, _uc = _build([webhook, disabled, active])

        await scheduler._sync_feeds()

        assert _feed_job_ids(scheduler) == {active.id}

    async def test_unschedules_removed_feed(self) -> None:
        feed = _polling_feed()
        scheduler, repo, _uc = _build([feed])
        await scheduler._sync_feeds()
        assert _feed_job_ids(scheduler) == {feed.id}

        repo.remove(feed.id)
        await scheduler._sync_feeds()
        assert _feed_job_ids(scheduler) == set()

    async def test_error_feeds_are_still_scheduled(self) -> None:
        feed = _polling_feed()
        feed.record_ingestion_failure("boom")
        assert feed.status == FeedStatus.ERROR
        scheduler, _repo, _uc = _build([feed])

        await scheduler._sync_feeds()

        assert _feed_job_ids(scheduler) == {feed.id}


class TestPoll:
    async def test_poll_runs_ingest_and_reschedules(self) -> None:
        feed = _polling_feed()
        scheduler, _repo, use_case = _build([feed])

        await scheduler._poll_feed(feed.id)

        assert use_case.calls == [feed.id]
        # A fresh one-shot job for the next poll should now exist.
        assert feed.id in _feed_job_ids(scheduler)

    async def test_poll_skips_missing_feed(self) -> None:
        scheduler, _repo, use_case = _build([])

        await scheduler._poll_feed("does-not-exist")

        assert use_case.calls == []
        assert _feed_job_ids(scheduler) == set()
