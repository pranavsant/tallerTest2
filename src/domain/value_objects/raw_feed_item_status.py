"""
RawFeedItemStatus value object.

Immutable enum-backed value object representing where a raw, ingested feed
item sits in the AI-analysis pipeline. Mirrors the ``raw_feed_items.status``
CHECK constraint.

Lifecycle::

    pending ──▶ processing ──▶ analyzed
       │                          ▲
       └────────────▶ failed ─────┘  (retried)
"""
from __future__ import annotations

from enum import Enum


class RawFeedItemStatus(str, Enum):
    """Pipeline state of an ingested raw feed item."""

    # Freshly ingested and queued, awaiting AI analysis.
    PENDING = "pending"
    # Picked up by the analysis worker.
    PROCESSING = "processing"
    # Analysis completed successfully.
    ANALYZED = "analyzed"
    # Analysis failed; may be retried.
    FAILED = "failed"

    @classmethod
    def values(cls) -> tuple[str, ...]:
        return tuple(s.value for s in cls)

    @classmethod
    def is_valid(cls, value: str) -> bool:
        return value in cls.values()
