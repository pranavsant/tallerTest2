"""
Unit tests for the Feed entity and its invariants.
"""
from __future__ import annotations

import pytest

from src.domain.entities.feed import Feed
from src.domain.exceptions import (
    InvalidFeedNameError,
    InvalidFeedUrlError,
    InvalidPollingIntervalError,
)
from src.domain.value_objects.feed_source_type import FeedSourceType
from src.domain.value_objects.feed_status import FeedStatus


def _webhook_feed(**overrides: object) -> Feed:
    kwargs: dict[str, object] = {
        "name": "Sensor stream",
        "source_type": FeedSourceType.WEBHOOK,
        "endpoint_url": "https://example.com/hook",
    }
    kwargs.update(overrides)
    return Feed(**kwargs)  # type: ignore[arg-type]


class TestFeedConstruction:
    def test_creates_with_defaults(self) -> None:
        feed = _webhook_feed()
        assert feed.id
        assert feed.name == "Sensor stream"
        assert feed.source_type == FeedSourceType.WEBHOOK
        assert feed.status == FeedStatus.ACTIVE
        assert feed.is_enabled is True

    def test_strips_name_whitespace(self) -> None:
        assert _webhook_feed(name="  Trimmed  ").name == "Trimmed"

    def test_manual_feed_needs_no_url(self) -> None:
        feed = Feed(name="Manual entry", source_type=FeedSourceType.MANUAL)
        assert feed.endpoint_url is None


class TestNameValidation:
    def test_rejects_empty_name(self) -> None:
        with pytest.raises(InvalidFeedNameError):
            _webhook_feed(name="   ")

    def test_rejects_overlong_name(self) -> None:
        with pytest.raises(InvalidFeedNameError):
            _webhook_feed(name="x" * (Feed.MAX_NAME_LENGTH + 1))


class TestUrlValidation:
    def test_rejects_malformed_url(self) -> None:
        with pytest.raises(InvalidFeedUrlError):
            _webhook_feed(endpoint_url="not-a-url")

    def test_rejects_non_http_scheme(self) -> None:
        with pytest.raises(InvalidFeedUrlError):
            _webhook_feed(endpoint_url="ftp://example.com/x")

    def test_requires_url_for_webhook(self) -> None:
        with pytest.raises(InvalidFeedUrlError):
            Feed(name="No URL", source_type=FeedSourceType.WEBHOOK)

    def test_accepts_https_url(self) -> None:
        feed = _webhook_feed(endpoint_url="https://host.example/path?x=1")
        assert feed.endpoint_url == "https://host.example/path?x=1"

    def test_switching_to_manual_allows_clearing_url(self) -> None:
        feed = _webhook_feed()
        feed.source_type = FeedSourceType.MANUAL
        feed.endpoint_url = None
        assert feed.endpoint_url is None


class TestPollingIntervalValidation:
    def test_rejects_too_small(self) -> None:
        with pytest.raises(InvalidPollingIntervalError):
            _webhook_feed(polling_interval_seconds=Feed.MIN_POLLING_INTERVAL_SECONDS - 1)

    def test_rejects_too_large(self) -> None:
        with pytest.raises(InvalidPollingIntervalError):
            _webhook_feed(polling_interval_seconds=Feed.MAX_POLLING_INTERVAL_SECONDS + 1)

    def test_accepts_in_bounds(self) -> None:
        feed = _webhook_feed(polling_interval_seconds=60)
        assert feed.polling_interval_seconds == 60

    def test_none_is_allowed(self) -> None:
        assert _webhook_feed().polling_interval_seconds is None


class TestEnableDisable:
    def test_disable_preserves_record_and_sets_status(self) -> None:
        feed = _webhook_feed()
        feed.disable()
        assert feed.is_enabled is False
        assert feed.status == FeedStatus.DISABLED

    def test_enable_restores_active_status(self) -> None:
        feed = _webhook_feed()
        feed.disable()
        feed.enable()
        assert feed.is_enabled is True
        assert feed.status == FeedStatus.ACTIVE

    def test_enable_leaves_error_status_untouched(self) -> None:
        feed = _webhook_feed(status=FeedStatus.ERROR, is_enabled=False)
        feed.enable()
        assert feed.is_enabled is True
        assert feed.status == FeedStatus.ERROR
