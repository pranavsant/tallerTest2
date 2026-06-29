"""
JsonApiFeedFetcher

Pulls items from an HTTP JSON API and shapes each element into a
:class:`FetchedItemDTO`. The response shape is described declaratively in the
feed's ``config`` so a single fetcher serves many APIs:

    config = {
        "format": "json",
        "items_path": "data.results",   # dot-path to the list of items
        "field_map": {                  # item field → source key (dot-path)
            "title": "headline",
            "content": "body",
            "url": "permalink",
            "external_id": "id",
            "published_at": "created_at",
        },
        "headers": {"Authorization": "Bearer …"},  # optional request headers
    }

When ``items_path`` is omitted the root must itself be a JSON array. Unmapped
fields are simply left empty; the whole element is preserved under ``raw``.

Selection: handles polling feeds whose ``config.format`` is ``"json"``/``"api"``.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

import httpx

from src.application.dtos.ingestion_dtos import FetchedItemDTO
from src.application.ports.feed_fetcher import IFeedFetcher
from src.domain.entities.feed import Feed

logger = logging.getLogger(__name__)

_JSON_FORMATS = ("json", "api")

_DEFAULT_FIELD_MAP = {
    "title": "title",
    "content": "content",
    "url": "url",
    "external_id": "id",
    "published_at": "published_at",
}


class JsonApiFeedFetcher(IFeedFetcher):
    """Fetches and maps JSON API responses."""

    def __init__(self, *, timeout_seconds: float = 15.0) -> None:
        self._timeout = timeout_seconds

    def supports(self, feed: Feed) -> bool:
        if not feed.source_type.is_polling() or not feed.endpoint_url:
            return False
        return str(feed.config.get("format", "")).lower() in _JSON_FORMATS

    async def fetch(self, feed: Feed) -> list[FetchedItemDTO]:
        assert feed.endpoint_url is not None  # guarded by supports()
        config = feed.config
        headers = {"User-Agent": "OverseerAI/0.1 (+feeds)"}
        extra = config.get("headers")
        if isinstance(extra, dict):
            headers.update({str(k): str(v) for k, v in extra.items()})

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.get(feed.endpoint_url, headers=headers)
            response.raise_for_status()
            payload = response.json()

        raw_items = self._extract_items(payload, config.get("items_path"))
        field_map = {**_DEFAULT_FIELD_MAP, **(config.get("field_map") or {})}
        return [self._map_item(el, field_map) for el in raw_items]

    # ── Mapping ─────────────────────────────────────────────────────────────

    @staticmethod
    def _extract_items(payload: Any, items_path: str | None) -> list[Any]:
        node = payload
        if items_path:
            for key in items_path.split("."):
                if not isinstance(node, dict):
                    return []
                node = node.get(key)
        if isinstance(node, list):
            return [el for el in node if isinstance(el, dict)]
        return []

    @staticmethod
    def _map_item(el: dict[str, Any], field_map: dict[str, str]) -> FetchedItemDTO:
        def lookup(field: str) -> Any:
            source_key = field_map.get(field)
            if not source_key:
                return None
            node: Any = el
            for key in str(source_key).split("."):
                if not isinstance(node, dict):
                    return None
                node = node.get(key)
            return node

        published = _coerce_dt(lookup("published_at"))
        return FetchedItemDTO(
            title=_coerce_str(lookup("title")),
            content=_coerce_str(lookup("content")),
            url=_coerce_str(lookup("url")),
            external_id=_coerce_str(lookup("external_id")),
            published_at=published,
            raw=el,
        )


def _coerce_str(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _coerce_dt(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    try:
        dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
