"""
SupabaseRawFeedItemRepository

Implements IRawFeedItemRepository using Supabase (PostgreSQL).
Maps DB rows ↔ RawFeedItem domain entities.
Infrastructure errors are caught and re-raised as RuntimeError so they never
leak the SDK type.

Deduplication relies on the ``uq_raw_feed_items_feed_content_hash`` UNIQUE
constraint: ``add_if_new`` issues an ``upsert`` with ``ignore_duplicates`` on
that constraint and infers novelty from whether a row came back.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from supabase import AsyncClient

from src.domain.entities.raw_feed_item import RawFeedItem
from src.domain.repositories.raw_feed_item_repository import IRawFeedItemRepository
from src.domain.value_objects.raw_feed_item_status import RawFeedItemStatus

_TABLE = "raw_feed_items"
_CONFLICT = "feed_id,content_hash"


class SupabaseRawFeedItemRepository(IRawFeedItemRepository):
    """Supabase-backed implementation of IRawFeedItemRepository."""

    def __init__(self, client: AsyncClient) -> None:
        self._client = client

    # ── IRawFeedItemRepository implementation ──────────────────────────────

    async def add_if_new(self, item: RawFeedItem) -> bool:
        """Insert *item*, skipping it if its (feed_id, content_hash) exists.

        Atomicity is provided by the unique constraint: ``ignore_duplicates``
        turns a conflicting insert into a no-op rather than an error, and the
        empty result set tells us the row was a duplicate.
        """
        row = self._to_row(item)
        try:
            result = (
                await self._client.table(_TABLE)
                .upsert(row, on_conflict=_CONFLICT, ignore_duplicates=True)
                .execute()
            )
        except Exception as exc:
            raise RuntimeError(
                f"Failed to insert raw feed item '{item.id}': {exc}"
            ) from exc

        # ignore_duplicates returns the inserted rows; an empty list means the
        # item already existed and was skipped.
        return bool(result.data)

    async def exists_by_content_hash(self, feed_id: str, content_hash: str) -> bool:
        try:
            result = (
                await self._client.table(_TABLE)
                .select("id")
                .eq("feed_id", feed_id)
                .eq("content_hash", content_hash)
                .limit(1)
                .execute()
            )
        except Exception as exc:
            raise RuntimeError(
                f"Failed to check raw feed item existence: {exc}"
            ) from exc

        return len(result.data) > 0

    async def get_by_id(self, item_id: str) -> RawFeedItem | None:
        try:
            result = (
                await self._client.table(_TABLE)
                .select("*")
                .eq("id", item_id)
                .limit(1)
                .execute()
            )
        except Exception as exc:
            raise RuntimeError(
                f"Failed to fetch raw feed item '{item_id}': {exc}"
            ) from exc

        if not result.data:
            return None
        return self._to_entity(result.data[0])

    async def list_by_status(
        self,
        status: RawFeedItemStatus,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> list[RawFeedItem]:
        try:
            result = (
                await self._client.table(_TABLE)
                .select("*")
                .eq("status", status.value)
                .range(offset, offset + limit - 1)
                .execute()
            )
        except Exception as exc:
            raise RuntimeError(
                f"Failed to list raw feed items by status: {exc}"
            ) from exc

        return [self._to_entity(row) for row in result.data]

    async def save(self, item: RawFeedItem) -> None:
        row = self._to_row(item)
        try:
            await self._client.table(_TABLE).upsert(row, on_conflict="id").execute()
        except Exception as exc:
            raise RuntimeError(
                f"Failed to save raw feed item '{item.id}': {exc}"
            ) from exc

    # ── Private mapping helpers ────────────────────────────────────────────

    @staticmethod
    def _to_row(item: RawFeedItem) -> dict[str, Any]:
        return {
            "id": item.id,
            "feed_id": item.feed_id,
            "content_hash": item.content_hash,
            "external_id": item.external_id,
            "title": item.title,
            "content": item.content,
            "url": item.url,
            "published_at": (
                item.published_at.isoformat()
                if item.published_at is not None
                else None
            ),
            "raw": item.raw,
            "status": item.status.value,
            "error": item.error,
            "created_at": item.created_at.isoformat(),
        }

    @staticmethod
    def _to_entity(row: dict[str, Any]) -> RawFeedItem:
        return RawFeedItem(
            item_id=row["id"],
            feed_id=row["feed_id"],
            content_hash=row["content_hash"],
            external_id=row.get("external_id"),
            title=row.get("title"),
            content=row.get("content"),
            url=row.get("url"),
            published_at=_parse_dt(row.get("published_at")),
            raw=dict(row.get("raw") or {}),
            status=RawFeedItemStatus(row["status"]),
            error=row.get("error"),
            created_at=_parse_dt(row["created_at"]),
        )


def _parse_dt(value: str | None) -> datetime | None:
    if value is None:
        return None
    return datetime.fromisoformat(value).replace(tzinfo=timezone.utc)
