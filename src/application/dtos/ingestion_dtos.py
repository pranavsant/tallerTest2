"""
Ingestion DTOs — typed contracts for the feed-ingestion pipeline.

Pure dataclasses; no domain or infrastructure imports.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class FetchedItemDTO:
    """A single item pulled from a feed source, before normalisation.

    Fetchers (RSS, webhook, API) translate their source-specific payloads into
    this shape. ``external_id`` is the source's own identifier when available
    and is preferred for deduplication; otherwise title/content/url are used.
    """

    title: str | None = None
    content: str | None = None
    url: str | None = None
    external_id: str | None = None
    published_at: datetime | None = None
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class IngestFeedResultDTO:
    """Outcome of polling a single feed once."""

    feed_id: str
    fetched: int
    new_items: int
    duplicates: int
    succeeded: bool
    error: str | None = None
