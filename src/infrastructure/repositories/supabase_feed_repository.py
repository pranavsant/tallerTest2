"""
SupabaseFeedRepository

Implements IFeedRepository using Supabase (PostgreSQL).
Maps DB rows ↔ Feed domain entities.
Infrastructure errors are caught and re-raised so they never leak the SDK type.

The ``feeds`` table has no dedicated polling-interval column, so the entity's
``polling_interval_seconds`` is persisted inside the ``config`` JSONB under the
reserved ``polling_interval_seconds`` key and lifted back out on read.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from supabase import AsyncClient

from src.domain.entities.feed import Feed
from src.domain.exceptions import FeedNotFoundError
from src.domain.repositories.feed_repository import IFeedRepository
from src.domain.value_objects.feed_source_type import FeedSourceType
from src.domain.value_objects.feed_status import FeedStatus

_TABLE = "feeds"
_INTERVAL_KEY = "polling_interval_seconds"


class SupabaseFeedRepository(IFeedRepository):
    """Supabase-backed implementation of IFeedRepository."""

    def __init__(self, client: AsyncClient) -> None:
        self._client = client

    # ── IFeedRepository implementation ─────────────────────────────────────

    async def save(self, feed: Feed) -> None:
        row = self._to_row(feed)
        try:
            await self._client.table(_TABLE).upsert(row, on_conflict="id").execute()
        except Exception as exc:
            raise RuntimeError(f"Failed to save feed '{feed.id}': {exc}") from exc

    async def get_by_id(self, feed_id: str) -> Feed | None:
        try:
            result = (
                await self._client.table(_TABLE)
                .select("*")
                .eq("id", feed_id)
                .limit(1)
                .execute()
            )
        except Exception as exc:
            raise RuntimeError(f"Failed to fetch feed '{feed_id}': {exc}") from exc

        if not result.data:
            return None
        return self._to_entity(result.data[0])

    async def list_by_status(
        self,
        status: FeedStatus,
        *,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Feed]:
        try:
            result = (
                await self._client.table(_TABLE)
                .select("*")
                .eq("status", status.value)
                .range(offset, offset + limit - 1)
                .execute()
            )
        except Exception as exc:
            raise RuntimeError(f"Failed to list feeds by status: {exc}") from exc

        return [self._to_entity(row) for row in result.data]

    async def list_all(self, *, limit: int = 50, offset: int = 0) -> list[Feed]:
        try:
            result = (
                await self._client.table(_TABLE)
                .select("*")
                .range(offset, offset + limit - 1)
                .execute()
            )
        except Exception as exc:
            raise RuntimeError(f"Failed to list feeds: {exc}") from exc

        return [self._to_entity(row) for row in result.data]

    async def delete(self, feed_id: str) -> None:
        if not await self.exists(feed_id):
            raise FeedNotFoundError(f"Feed '{feed_id}' not found")
        try:
            await self._client.table(_TABLE).delete().eq("id", feed_id).execute()
        except Exception as exc:
            raise RuntimeError(f"Failed to delete feed '{feed_id}': {exc}") from exc

    async def exists(self, feed_id: str) -> bool:
        try:
            result = (
                await self._client.table(_TABLE)
                .select("id")
                .eq("id", feed_id)
                .limit(1)
                .execute()
            )
        except Exception as exc:
            raise RuntimeError(f"Failed to check feed existence: {exc}") from exc

        return len(result.data) > 0

    # ── Private mapping helpers ────────────────────────────────────────────

    @staticmethod
    def _to_row(feed: Feed) -> dict[str, Any]:
        config = feed.config
        if feed.polling_interval_seconds is not None:
            config[_INTERVAL_KEY] = feed.polling_interval_seconds
        else:
            config.pop(_INTERVAL_KEY, None)

        return {
            "id": feed.id,
            "name": feed.name,
            "source_type": feed.source_type.value,
            "status": feed.status.value,
            "endpoint_url": feed.endpoint_url,
            "config": config,
            "is_enabled": feed.is_enabled,
            "last_ingested_at": (
                feed.last_ingested_at.isoformat()
                if feed.last_ingested_at is not None
                else None
            ),
            "created_at": feed.created_at.isoformat(),
            "updated_at": feed.updated_at.isoformat(),
        }

    @staticmethod
    def _to_entity(row: dict[str, Any]) -> Feed:
        config = dict(row.get("config") or {})
        polling_interval = config.pop(_INTERVAL_KEY, None)

        return Feed(
            feed_id=row["id"],
            name=row["name"],
            source_type=FeedSourceType(row["source_type"]),
            endpoint_url=row.get("endpoint_url"),
            polling_interval_seconds=(
                int(polling_interval) if polling_interval is not None else None
            ),
            config=config,
            status=FeedStatus(row["status"]),
            is_enabled=bool(row["is_enabled"]),
            last_ingested_at=_parse_dt(row.get("last_ingested_at")),
            created_at=_parse_dt(row["created_at"]),
            updated_at=_parse_dt(row["updated_at"]),
        )


def _parse_dt(value: str | None) -> datetime | None:
    if value is None:
        return None
    return datetime.fromisoformat(value).replace(tzinfo=timezone.utc)
