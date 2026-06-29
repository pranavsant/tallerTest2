"""
Unit tests for the RSS and JSON-API feed fetchers.

HTTP is faked with httpx.MockTransport so the tests are offline and fast.
"""
from __future__ import annotations

import httpx
import pytest

from src.domain.entities.feed import Feed
from src.domain.value_objects.feed_source_type import FeedSourceType
from src.infrastructure.fetchers.json_api_feed_fetcher import JsonApiFeedFetcher
from src.infrastructure.fetchers.rss_feed_fetcher import RssFeedFetcher

RSS_BODY = """<?xml version="1.0"?>
<rss version="2.0"><channel>
  <title>Example</title>
  <item>
    <title>First post</title>
    <description>Body one</description>
    <link>https://example.com/1</link>
    <guid>guid-1</guid>
    <pubDate>Mon, 01 Jan 2024 12:00:00 GMT</pubDate>
  </item>
  <item>
    <title>Second post</title>
    <description>Body two</description>
    <link>https://example.com/2</link>
    <guid>guid-2</guid>
  </item>
</channel></rss>
"""

ATOM_BODY = """<?xml version="1.0"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <title>Example</title>
  <entry>
    <title>Atom post</title>
    <summary>Atom body</summary>
    <id>atom-1</id>
    <link href="https://example.com/a1"/>
    <updated>2024-01-01T12:00:00Z</updated>
  </entry>
</feed>
"""


def _polling_feed(**config: object) -> Feed:
    return Feed(
        name="Poller",
        source_type=FeedSourceType.POLLING,
        endpoint_url="https://example.com/feed",
        polling_interval_seconds=60,
        config=config or None,
    )


def _patch_transport(monkeypatch: pytest.MonkeyPatch, handler) -> None:  # type: ignore[no-untyped-def]
    """Force httpx.AsyncClient to use a MockTransport for these tests."""
    real_init = httpx.AsyncClient.__init__

    def patched(self, *args, **kwargs):  # type: ignore[no-untyped-def]
        kwargs["transport"] = httpx.MockTransport(handler)
        real_init(self, *args, **kwargs)

    monkeypatch.setattr(httpx.AsyncClient, "__init__", patched)


# ── RSS fetcher ───────────────────────────────────────────────────────────────


class TestRssFetcherSelection:
    def test_supports_default_polling_feed(self) -> None:
        assert RssFeedFetcher().supports(_polling_feed()) is True

    def test_supports_explicit_rss_format(self) -> None:
        assert RssFeedFetcher().supports(_polling_feed(format="rss")) is True

    def test_does_not_support_json_format(self) -> None:
        assert RssFeedFetcher().supports(_polling_feed(format="json")) is False

    def test_does_not_support_webhook(self) -> None:
        feed = Feed(
            name="Hook",
            source_type=FeedSourceType.WEBHOOK,
            endpoint_url="https://example.com/hook",
        )
        assert RssFeedFetcher().supports(feed) is False


class TestRssFetcherParsing:
    async def test_parses_rss_items(self, monkeypatch: pytest.MonkeyPatch) -> None:
        _patch_transport(
            monkeypatch, lambda req: httpx.Response(200, text=RSS_BODY)
        )
        items = await RssFeedFetcher().fetch(_polling_feed())
        assert len(items) == 2
        assert items[0].title == "First post"
        assert items[0].content == "Body one"
        assert items[0].url == "https://example.com/1"
        assert items[0].external_id == "guid-1"
        assert items[0].published_at is not None
        # Second item has no pubDate → None, falls back to guid for id.
        assert items[1].published_at is None
        assert items[1].external_id == "guid-2"

    async def test_parses_atom_entries(self, monkeypatch: pytest.MonkeyPatch) -> None:
        _patch_transport(
            monkeypatch, lambda req: httpx.Response(200, text=ATOM_BODY)
        )
        items = await RssFeedFetcher().fetch(_polling_feed())
        assert len(items) == 1
        assert items[0].title == "Atom post"
        assert items[0].content == "Atom body"
        assert items[0].url == "https://example.com/a1"
        assert items[0].external_id == "atom-1"

    async def test_raises_on_http_error(self, monkeypatch: pytest.MonkeyPatch) -> None:
        _patch_transport(monkeypatch, lambda req: httpx.Response(503))
        with pytest.raises(httpx.HTTPStatusError):
            await RssFeedFetcher().fetch(_polling_feed())


# ── JSON API fetcher ────────────────────────────────────────────────────────


class TestJsonApiFetcher:
    def test_selection_requires_json_format(self) -> None:
        assert JsonApiFeedFetcher().supports(_polling_feed(format="json")) is True
        assert JsonApiFeedFetcher().supports(_polling_feed(format="api")) is True
        assert JsonApiFeedFetcher().supports(_polling_feed()) is False

    async def test_maps_items_with_path_and_field_map(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        payload = {
            "data": {
                "results": [
                    {"id": "1", "headline": "H1", "body": "B1", "permalink": "u1"},
                    {"id": "2", "headline": "H2", "body": "B2", "permalink": "u2"},
                ]
            }
        }
        _patch_transport(monkeypatch, lambda req: httpx.Response(200, json=payload))
        feed = _polling_feed(
            format="json",
            items_path="data.results",
            field_map={
                "title": "headline",
                "content": "body",
                "url": "permalink",
                "external_id": "id",
            },
        )
        items = await JsonApiFeedFetcher().fetch(feed)
        assert len(items) == 2
        assert items[0].title == "H1"
        assert items[0].content == "B1"
        assert items[0].url == "u1"
        assert items[0].external_id == "1"
        assert items[0].raw == payload["data"]["results"][0]

    async def test_root_array_with_default_field_map(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        payload = [{"id": "x", "title": "T", "content": "C"}]
        _patch_transport(monkeypatch, lambda req: httpx.Response(200, json=payload))
        items = await JsonApiFeedFetcher().fetch(_polling_feed(format="json"))
        assert len(items) == 1
        assert items[0].title == "T"
        assert items[0].external_id == "x"

    async def test_missing_items_path_yields_nothing(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _patch_transport(
            monkeypatch, lambda req: httpx.Response(200, json={"other": 1})
        )
        feed = _polling_feed(format="json", items_path="data.results")
        items = await JsonApiFeedFetcher().fetch(feed)
        assert items == []
