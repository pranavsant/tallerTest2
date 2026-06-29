"""
FeedSourceType value object.

Immutable enum-backed value object enumerating the kinds of ingestion source a
Feed can represent. Mirrors the ``feeds.source_type`` CHECK constraint.
"""
from __future__ import annotations

from enum import Enum


class FeedSourceType(str, Enum):
    """The recognised feed source types."""

    WEBHOOK = "webhook"
    POLLING = "polling"
    STREAM = "stream"
    MANUAL = "manual"

    @classmethod
    def values(cls) -> tuple[str, ...]:
        return tuple(t.value for t in cls)

    @classmethod
    def is_valid(cls, value: str) -> bool:
        return value in cls.values()

    def requires_endpoint(self) -> bool:
        """Whether a source of this type is driven by an endpoint URL.

        Webhook, polling, and stream sources are reached over the network and
        therefore require an endpoint; manual feeds are populated by hand.
        """
        return self in (
            FeedSourceType.WEBHOOK,
            FeedSourceType.POLLING,
            FeedSourceType.STREAM,
        )

    def is_polling(self) -> bool:
        """Whether this source is polled on an interval."""
        return self == FeedSourceType.POLLING
