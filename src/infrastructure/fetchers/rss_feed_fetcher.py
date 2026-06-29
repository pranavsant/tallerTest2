"""
RssFeedFetcher

Pulls items from an RSS 2.0 or Atom feed over HTTP and shapes each entry into
a :class:`FetchedItemDTO`. Parsing uses the standard-library XML parser
(``xml.etree.ElementTree``) so no extra dependency is required.

Selection: handles polling feeds whose ``config.format`` is ``"rss"``/``"atom"``
or is absent (RSS is the default polling format).
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from xml.etree import ElementTree

import httpx

from src.application.dtos.ingestion_dtos import FetchedItemDTO
from src.application.ports.feed_fetcher import IFeedFetcher
from src.domain.entities.feed import Feed

logger = logging.getLogger(__name__)

# Atom uses a namespace; RSS 2.0 does not.
_ATOM_NS = "{http://www.w3.org/2005/Atom}"

_RSS_FORMATS = ("rss", "atom", "")


class RssFeedFetcher(IFeedFetcher):
    """Fetches and parses RSS/Atom feeds."""

    def __init__(self, *, timeout_seconds: float = 15.0) -> None:
        self._timeout = timeout_seconds

    def supports(self, feed: Feed) -> bool:
        if not feed.source_type.is_polling() or not feed.endpoint_url:
            return False
        fmt = str(feed.config.get("format", "")).lower()
        return fmt in _RSS_FORMATS

    async def fetch(self, feed: Feed) -> list[FetchedItemDTO]:
        assert feed.endpoint_url is not None  # guarded by supports()
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.get(
                feed.endpoint_url, headers={"User-Agent": "OverseerAI/0.1 (+feeds)"}
            )
            response.raise_for_status()
            body = response.text

        return self._parse(body)

    # ── Parsing ─────────────────────────────────────────────────────────────

    def _parse(self, body: str) -> list[FetchedItemDTO]:
        root = ElementTree.fromstring(body)

        # RSS 2.0: <rss><channel><item>… ; Atom: <feed><entry>…
        items = root.findall(".//item")
        if items:
            return [self._parse_rss_item(el) for el in items]

        entries = root.findall(f".//{_ATOM_NS}entry")
        return [self._parse_atom_entry(el) for el in entries]

    @staticmethod
    def _parse_rss_item(el: ElementTree.Element) -> FetchedItemDTO:
        title = _text(el.find("title"))
        content = _text(el.find("description"))
        link = _text(el.find("link"))
        guid = _text(el.find("guid"))
        published = _parse_rss_date(_text(el.find("pubDate")))
        return FetchedItemDTO(
            title=title,
            content=content,
            url=link,
            external_id=guid or link,
            published_at=published,
            raw={
                "title": title,
                "description": content,
                "link": link,
                "guid": guid,
            },
        )

    @staticmethod
    def _parse_atom_entry(el: ElementTree.Element) -> FetchedItemDTO:
        title = _text(el.find(f"{_ATOM_NS}title"))
        content = _text(el.find(f"{_ATOM_NS}summary")) or _text(
            el.find(f"{_ATOM_NS}content")
        )
        entry_id = _text(el.find(f"{_ATOM_NS}id"))
        link_el = el.find(f"{_ATOM_NS}link")
        link = link_el.get("href") if link_el is not None else None
        published = _parse_iso_date(
            _text(el.find(f"{_ATOM_NS}updated"))
            or _text(el.find(f"{_ATOM_NS}published"))
        )
        return FetchedItemDTO(
            title=title,
            content=content,
            url=link,
            external_id=entry_id or link,
            published_at=published,
            raw={
                "title": title,
                "summary": content,
                "id": entry_id,
                "link": link,
            },
        )


def _text(el: ElementTree.Element | None) -> str | None:
    if el is None or el.text is None:
        return None
    stripped = el.text.strip()
    return stripped or None


def _parse_rss_date(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        dt = parsedate_to_datetime(value)
    except (TypeError, ValueError):
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def _parse_iso_date(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        # Normalise a trailing 'Z' which fromisoformat rejects on older runtimes.
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt
