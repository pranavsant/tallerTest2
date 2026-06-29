"""
RawFeedItem entity.

A RawFeedItem is a single unit of content pulled from a Feed source (one RSS
entry, one webhook delivery, one element of an API response) **after** it has
been normalised into the platform's standard schema. Every raw item is queued
for downstream AI analysis; its :class:`RawFeedItemStatus` tracks where it is
in that pipeline.

Standard normalised schema
--------------------------
- ``external_id``  — the source's own identifier for the item, when one exists
- ``title``        — short human-readable headline
- ``content``      — the main body / payload text
- ``url``          — canonical link back to the item at the source, if any
- ``published_at`` — when the source says the item was published
- ``raw``          — the untouched source payload, retained for re-processing

Deduplication
-------------
Each item carries a ``content_hash``: a stable SHA-256 digest derived from the
identifying parts of the normalised item. Two ingests of the same underlying
item produce the same hash, so the repository can reject duplicates with a
single uniqueness check (see :meth:`compute_content_hash`).

The entity protects its own invariants:
- ``feed_id`` is required (an item always belongs to a feed)
- ``content_hash`` is required and non-empty
- at least one of ``title`` / ``content`` must be present (an item with no
  textual signal is not worth analysing)
"""
from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timezone
from typing import Any

from src.domain.exceptions import (
    EmptyFeedItemError,
    InvalidContentHashError,
    MissingFeedReferenceError,
)
from src.domain.value_objects.raw_feed_item_status import RawFeedItemStatus


class RawFeedItem:
    """A normalised, deduplicated unit of feed content awaiting AI analysis."""

    def __init__(
        self,
        *,
        item_id: str | None = None,
        feed_id: str,
        content_hash: str,
        title: str | None = None,
        content: str | None = None,
        url: str | None = None,
        external_id: str | None = None,
        published_at: datetime | None = None,
        raw: dict[str, Any] | None = None,
        status: RawFeedItemStatus = RawFeedItemStatus.PENDING,
        error: str | None = None,
        created_at: datetime | None = None,
    ) -> None:
        if not feed_id:
            raise MissingFeedReferenceError(
                "A raw feed item must reference the feed it came from"
            )

        normalised_hash = content_hash.strip() if content_hash else ""
        if not normalised_hash:
            raise InvalidContentHashError("content_hash must be a non-empty string")

        self._title = title.strip() if title else None
        self._content = content.strip() if content else None
        if not self._title and not self._content:
            raise EmptyFeedItemError(
                "A raw feed item must have a title or content to be ingested"
            )

        self._id = item_id or str(uuid.uuid4())
        self._feed_id = feed_id
        self._content_hash = normalised_hash
        self._url = url.strip() if url else None
        self._external_id = external_id.strip() if external_id else None
        self._published_at = published_at
        self._raw = dict(raw) if raw else {}
        self._status = status
        self._error = error
        self._created_at = created_at or datetime.now(timezone.utc)

    # ── Identity & immutable attributes ─────────────────────────────────────

    @property
    def id(self) -> str:
        return self._id

    @property
    def feed_id(self) -> str:
        return self._feed_id

    @property
    def content_hash(self) -> str:
        return self._content_hash

    @property
    def title(self) -> str | None:
        return self._title

    @property
    def content(self) -> str | None:
        return self._content

    @property
    def url(self) -> str | None:
        return self._url

    @property
    def external_id(self) -> str | None:
        return self._external_id

    @property
    def published_at(self) -> datetime | None:
        return self._published_at

    @property
    def raw(self) -> dict[str, Any]:
        return dict(self._raw)

    @property
    def created_at(self) -> datetime:
        return self._created_at

    # ── Pipeline status ─────────────────────────────────────────────────────

    @property
    def status(self) -> RawFeedItemStatus:
        return self._status

    @property
    def error(self) -> str | None:
        return self._error

    def mark_processing(self) -> None:
        """Move the item into the in-flight analysis state."""
        self._status = RawFeedItemStatus.PROCESSING
        self._error = None

    def mark_analyzed(self) -> None:
        """Record that AI analysis completed successfully."""
        self._status = RawFeedItemStatus.ANALYZED
        self._error = None

    def mark_failed(self, error: str) -> None:
        """Record that analysis failed, retaining the reason."""
        self._status = RawFeedItemStatus.FAILED
        self._error = error

    # ── Deduplication ───────────────────────────────────────────────────────

    @staticmethod
    def compute_content_hash(
        feed_id: str,
        *,
        external_id: str | None = None,
        title: str | None = None,
        content: str | None = None,
        url: str | None = None,
    ) -> str:
        """Derive the stable dedup hash for a (would-be) item.

        The hash is scoped to ``feed_id`` so identical content from two
        different feeds is not collapsed. When the source supplies its own
        ``external_id`` that alone identifies the item; otherwise the digest
        falls back to the normalised title/content/url so re-fetching an
        unchanged item yields the same hash.
        """
        if external_id:
            identifying = external_id.strip()
        else:
            identifying = "\x1f".join(
                part.strip()
                for part in (title or "", content or "", url or "")
            )

        digest = hashlib.sha256(f"{feed_id}\x1f{identifying}".encode()).hexdigest()
        return digest

    def __repr__(self) -> str:
        return (
            f"RawFeedItem(id={self._id!r}, feed_id={self._feed_id!r}, "
            f"status={self._status}, title={self._title!r})"
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, RawFeedItem):
            return NotImplemented
        return self._id == other._id

    def __hash__(self) -> int:
        return hash(self._id)
