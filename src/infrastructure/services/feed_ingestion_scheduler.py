"""
FeedIngestionScheduler

The background polling worker (acceptance criteria 2 & 5). Wraps an
APScheduler ``AsyncIOScheduler`` running on the application's asyncio loop and
drives the :class:`IngestFeedUseCase` for every active polling feed.

Design
------
- On startup a recurring **sync** job (re)discovers which feeds should be
  polled. Feeds added/removed/enabled/disabled via the CRUD API are picked up
  on the next sync without a restart.
- Each pollable feed gets its own job whose interval is the feed's effective
  cadence. After every poll the job **reschedules itself** using
  ``feed.next_poll_delay_seconds()`` so exponential backoff on a failing feed
  takes effect immediately, and a recovered feed returns to its normal cadence.
- All scheduling state lives in the scheduler; the use case and domain stay
  free of any APScheduler knowledge.

This is infrastructure: it composes domain repositories and an application use
case, but contains no business rules of its own.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from src.application.use_cases.ingest_feed import IngestFeedUseCase
from src.domain.entities.feed import Feed
from src.domain.repositories.feed_repository import IFeedRepository
from src.domain.value_objects.feed_status import FeedStatus

logger = logging.getLogger(__name__)

_SYNC_JOB_ID = "feed-ingestion-sync"
_FEED_JOB_PREFIX = "feed-poll:"


class FeedIngestionScheduler:
    """APScheduler-backed background poller for feed ingestion."""

    def __init__(
        self,
        *,
        feed_repository: IFeedRepository,
        ingest_use_case: IngestFeedUseCase,
        sync_interval_seconds: int = 60,
    ) -> None:
        self._feeds = feed_repository
        self._ingest = ingest_use_case
        self._sync_interval = sync_interval_seconds
        self._scheduler = AsyncIOScheduler(timezone="UTC")

    # ── Lifecycle ───────────────────────────────────────────────────────────

    def start(self) -> None:
        """Start the scheduler and register the recurring feed-sync job."""
        if self._scheduler.running:
            return
        self._scheduler.add_job(
            self._sync_feeds,
            trigger="interval",
            seconds=self._sync_interval,
            id=_SYNC_JOB_ID,
            # Fire once immediately on startup so polling begins without
            # waiting a full sync interval.
            next_run_time=_now(),
            max_instances=1,
            coalesce=True,
            replace_existing=True,
        )
        self._scheduler.start()
        logger.info(
            "Feed ingestion scheduler started (sync every %ds)", self._sync_interval
        )

    def shutdown(self) -> None:
        """Stop the scheduler, allowing in-flight jobs to finish."""
        if self._scheduler.running:
            self._scheduler.shutdown(wait=False)
            logger.info("Feed ingestion scheduler stopped")

    # ── Sync: reconcile scheduled jobs with the active feed set ─────────────

    async def _sync_feeds(self) -> None:
        """Reconcile the set of per-feed poll jobs with the database."""
        try:
            feeds = await self._load_pollable_feeds()
        except Exception:  # noqa: BLE001 — never let a sync failure kill the loop
            logger.exception("Feed sync failed; will retry next interval")
            return

        wanted = {f.id: f for f in feeds}

        # Remove jobs for feeds that are gone or no longer pollable.
        for job in self._scheduler.get_jobs():
            if not job.id.startswith(_FEED_JOB_PREFIX):
                continue
            feed_id = job.id[len(_FEED_JOB_PREFIX) :]
            if feed_id not in wanted:
                self._scheduler.remove_job(job.id)
                logger.info("Unscheduled feed %s (no longer active)", feed_id)

        # Ensure a job exists for every pollable feed.
        for feed in feeds:
            job_id = _FEED_JOB_PREFIX + feed.id
            if self._scheduler.get_job(job_id) is None:
                self._schedule_feed(feed, first_run=_soon())
                logger.info(
                    "Scheduled feed %s (interval=%ds)",
                    feed.id,
                    feed.effective_interval_seconds(),
                )

    async def _load_pollable_feeds(self) -> list[Feed]:
        """All enabled, active polling feeds that should currently be polled."""
        # Active and error feeds are both candidates: an error feed must keep
        # being retried (with backoff). Paused/disabled feeds are excluded.
        feeds: list[Feed] = []
        for status in (FeedStatus.ACTIVE, FeedStatus.ERROR):
            feeds.extend(await self._feeds.list_by_status(status, limit=500))
        return [f for f in feeds if f.is_due_for_polling()]

    # ── Per-feed polling job ────────────────────────────────────────────────

    def _schedule_feed(self, feed: Feed, *, first_run: datetime) -> None:
        self._scheduler.add_job(
            self._poll_feed,
            trigger="date",
            run_date=first_run,
            args=[feed.id],
            id=_FEED_JOB_PREFIX + feed.id,
            max_instances=1,
            coalesce=True,
            replace_existing=True,
        )

    async def _poll_feed(self, feed_id: str) -> None:
        """Run one ingestion pass for *feed_id*, then reschedule the next pass.

        Reloads the feed each run so config/interval/enablement changes and the
        persisted backoff counter are always honoured. The next run is a
        one-shot job at ``now + next_poll_delay_seconds`` so backoff is applied
        per-feed without blocking other feeds.
        """
        feed = await self._feeds.get_by_id(feed_id)
        if feed is None or not feed.is_due_for_polling():
            # Feed was deleted or stood down between sync and run; drop the job.
            logger.info("Skipping poll for feed %s (gone or not due)", feed_id)
            return

        try:
            result = await self._ingest.execute(feed)
            if not result.succeeded:
                logger.warning(
                    "Feed %s poll reported failure: %s", feed_id, result.error
                )
        except Exception:  # noqa: BLE001 — a poll must never crash the loop
            logger.exception("Unexpected error polling feed %s", feed_id)

        # Reload to pick up the freshly-persisted backoff state, then reschedule.
        refreshed = await self._feeds.get_by_id(feed_id)
        if refreshed is None or not refreshed.is_due_for_polling():
            return
        delay = refreshed.next_poll_delay_seconds()
        self._schedule_feed(refreshed, first_run=_now() + timedelta(seconds=delay))
        logger.debug("Feed %s next poll in %ds", feed_id, delay)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _soon() -> datetime:
    # Stagger initial polls very slightly so a large feed set doesn't stampede.
    return _now() + timedelta(seconds=1)
