"""
Feed DTOs — typed contracts for feed-related use cases.
Pure dataclasses; no domain or infrastructure imports.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

# Sentinel distinguishing "field omitted" from "explicitly set to None" on
# update. ``UpdateFeedInputDTO`` uses it so a partial update can clear an
# optional attribute (e.g. set ``endpoint_url`` back to None) without every
# omitted field being treated as a clear.
_UNSET: Any = object()


# ── Inputs ────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class CreateFeedInputDTO:
    name: str
    source_type: str
    endpoint_url: str | None = None
    polling_interval_seconds: int | None = None
    config: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class UpdateFeedInputDTO:
    feed_id: str
    name: str | None = None
    source_type: str | None = None
    endpoint_url: str | None = _UNSET
    polling_interval_seconds: int | None = _UNSET
    config: dict[str, Any] | None = None


@dataclass(frozen=True)
class GetFeedInputDTO:
    feed_id: str


@dataclass(frozen=True)
class ListFeedsInputDTO:
    status_filter: str | None = None
    limit: int = 50
    offset: int = 0


@dataclass(frozen=True)
class DeleteFeedInputDTO:
    feed_id: str


@dataclass(frozen=True)
class SetFeedEnabledInputDTO:
    feed_id: str
    is_enabled: bool


# ── Outputs ───────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class FeedOutputDTO:
    feed_id: str
    name: str
    source_type: str
    status: str
    endpoint_url: str | None
    polling_interval_seconds: int | None
    config: dict[str, Any]
    is_enabled: bool
    last_ingested_at: datetime | None
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class FeedListOutputDTO:
    feeds: list[FeedOutputDTO]
    total: int
    limit: int
    offset: int
