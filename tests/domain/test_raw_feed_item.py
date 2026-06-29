"""
Unit tests for the RawFeedItem entity, its invariants, and dedup hashing.
"""
from __future__ import annotations

from datetime import datetime, timezone

import pytest

from src.domain.entities.raw_feed_item import RawFeedItem
from src.domain.exceptions import (
    EmptyFeedItemError,
    InvalidContentHashError,
    MissingFeedReferenceError,
)
from src.domain.value_objects.raw_feed_item_status import RawFeedItemStatus

FEED_ID = "11111111-1111-1111-1111-111111111111"


def _item(**overrides: object) -> RawFeedItem:
    kwargs: dict[str, object] = {
        "feed_id": FEED_ID,
        "content_hash": "abc123",
        "title": "A headline",
        "content": "Some body text",
    }
    kwargs.update(overrides)
    return RawFeedItem(**kwargs)  # type: ignore[arg-type]


class TestConstruction:
    def test_creates_with_defaults(self) -> None:
        item = _item()
        assert item.id
        assert item.feed_id == FEED_ID
        assert item.status == RawFeedItemStatus.PENDING
        assert item.error is None
        assert item.created_at.tzinfo is not None

    def test_strips_text_fields(self) -> None:
        item = _item(title="  Hi  ", content="  Body  ")
        assert item.title == "Hi"
        assert item.content == "Body"

    def test_title_only_is_allowed(self) -> None:
        item = _item(title="Just a title", content=None)
        assert item.content is None

    def test_content_only_is_allowed(self) -> None:
        item = _item(title=None, content="Just content")
        assert item.title is None


class TestInvariants:
    def test_rejects_missing_feed_id(self) -> None:
        with pytest.raises(MissingFeedReferenceError):
            _item(feed_id="")

    def test_rejects_empty_content_hash(self) -> None:
        with pytest.raises(InvalidContentHashError):
            _item(content_hash="   ")

    def test_rejects_item_with_no_text(self) -> None:
        with pytest.raises(EmptyFeedItemError):
            _item(title=None, content=None)


class TestStatusTransitions:
    def test_mark_processing(self) -> None:
        item = _item()
        item.mark_processing()
        assert item.status == RawFeedItemStatus.PROCESSING

    def test_mark_analyzed_clears_error(self) -> None:
        item = _item()
        item.mark_failed("boom")
        item.mark_analyzed()
        assert item.status == RawFeedItemStatus.ANALYZED
        assert item.error is None

    def test_mark_failed_records_reason(self) -> None:
        item = _item()
        item.mark_failed("network error")
        assert item.status == RawFeedItemStatus.FAILED
        assert item.error == "network error"


class TestContentHash:
    def test_external_id_drives_hash(self) -> None:
        h1 = RawFeedItem.compute_content_hash(FEED_ID, external_id="guid-1")
        h2 = RawFeedItem.compute_content_hash(
            FEED_ID, external_id="guid-1", title="different", content="different"
        )
        # When external_id is present, title/content are ignored.
        assert h1 == h2

    def test_same_content_same_hash(self) -> None:
        h1 = RawFeedItem.compute_content_hash(
            FEED_ID, title="t", content="c", url="u"
        )
        h2 = RawFeedItem.compute_content_hash(
            FEED_ID, title="t", content="c", url="u"
        )
        assert h1 == h2

    def test_different_content_different_hash(self) -> None:
        h1 = RawFeedItem.compute_content_hash(FEED_ID, title="a")
        h2 = RawFeedItem.compute_content_hash(FEED_ID, title="b")
        assert h1 != h2

    def test_hash_is_feed_scoped(self) -> None:
        h1 = RawFeedItem.compute_content_hash("feed-a", external_id="x")
        h2 = RawFeedItem.compute_content_hash("feed-b", external_id="x")
        assert h1 != h2

    def test_hash_is_sha256_hex(self) -> None:
        h = RawFeedItem.compute_content_hash(FEED_ID, external_id="x")
        assert len(h) == 64
        int(h, 16)  # parses as hex


def test_published_at_roundtrips() -> None:
    when = datetime(2024, 1, 1, tzinfo=timezone.utc)
    assert _item(published_at=when).published_at == when
