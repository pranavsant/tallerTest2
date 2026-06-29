"""
Unit tests for the Feed entity's ingestion/backoff behaviour.
"""
from __future__ import annotations

from src.domain.entities.feed import Feed
from src.domain.value_objects.feed_source_type import FeedSourceType
from src.domain.value_objects.feed_status import FeedStatus


def _polling_feed(**overrides: object) -> Feed:
    kwargs: dict[str, object] = {
        "name": "Poller",
        "source_type": FeedSourceType.POLLING,
        "endpoint_url": "https://example.com/rss",
        "polling_interval_seconds": 60,
    }
    kwargs.update(overrides)
    return Feed(**kwargs)  # type: ignore[arg-type]


class TestDueForPolling:
    def test_enabled_active_polling_feed_is_due(self) -> None:
        assert _polling_feed().is_due_for_polling() is True

    def test_disabled_feed_is_not_due(self) -> None:
        feed = _polling_feed()
        feed.disable()
        assert feed.is_due_for_polling() is False

    def test_non_polling_feed_is_not_due(self) -> None:
        feed = Feed(
            name="Hook",
            source_type=FeedSourceType.WEBHOOK,
            endpoint_url="https://example.com/hook",
        )
        assert feed.is_due_for_polling() is False

    def test_error_feed_still_polls(self) -> None:
        feed = _polling_feed()
        feed.record_ingestion_failure("boom")
        assert feed.status == FeedStatus.ERROR
        assert feed.is_due_for_polling() is True


class TestEffectiveInterval:
    def test_uses_configured_interval(self) -> None:
        assert _polling_feed(polling_interval_seconds=120).effective_interval_seconds() == 120

    def test_falls_back_to_default(self) -> None:
        feed = _polling_feed(polling_interval_seconds=None)
        assert (
            feed.effective_interval_seconds()
            == Feed.DEFAULT_POLLING_INTERVAL_SECONDS
        )


class TestBackoff:
    def test_no_failures_uses_interval(self) -> None:
        feed = _polling_feed(polling_interval_seconds=60)
        assert feed.next_poll_delay_seconds() == 60

    def test_delay_doubles_per_failure(self) -> None:
        feed = _polling_feed(polling_interval_seconds=60)
        feed.record_ingestion_failure("e1")
        assert feed.next_poll_delay_seconds() == 120
        feed.record_ingestion_failure("e2")
        assert feed.next_poll_delay_seconds() == 240
        feed.record_ingestion_failure("e3")
        assert feed.next_poll_delay_seconds() == 480

    def test_delay_capped_at_max(self) -> None:
        feed = _polling_feed(polling_interval_seconds=60)
        for i in range(20):
            feed.record_ingestion_failure(f"e{i}")
        assert feed.next_poll_delay_seconds() == Feed.MAX_BACKOFF_SECONDS

    def test_success_clears_backoff(self) -> None:
        feed = _polling_feed(polling_interval_seconds=60)
        feed.record_ingestion_failure("e1")
        feed.record_ingestion_failure("e2")
        assert feed.consecutive_failures == 2

        feed.record_ingestion_success()
        assert feed.consecutive_failures == 0
        assert feed.last_error is None
        assert feed.last_ingested_at is not None
        assert feed.next_poll_delay_seconds() == 60

    def test_failure_sets_error_state_and_message(self) -> None:
        feed = _polling_feed()
        feed.record_ingestion_failure("connection refused")
        assert feed.status == FeedStatus.ERROR
        assert feed.last_error == "connection refused"
        assert feed.consecutive_failures == 1

    def test_success_recovers_from_error_state(self) -> None:
        feed = _polling_feed()
        feed.record_ingestion_failure("boom")
        feed.record_ingestion_success()
        assert feed.status == FeedStatus.ACTIVE
