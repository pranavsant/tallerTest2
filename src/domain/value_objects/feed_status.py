"""
FeedStatus value object.

Immutable enum-backed value object representing the operational state of a
Feed. Mirrors the ``feeds.status`` CHECK constraint.
"""
from __future__ import annotations

from enum import Enum


class FeedStatus(str, Enum):
    """Possible operational states a Feed can be in."""

    ACTIVE = "active"
    PAUSED = "paused"
    ERROR = "error"
    DISABLED = "disabled"

    @classmethod
    def values(cls) -> tuple[str, ...]:
        return tuple(s.value for s in cls)

    @classmethod
    def is_valid(cls, value: str) -> bool:
        return value in cls.values()
