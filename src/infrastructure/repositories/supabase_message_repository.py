"""
SupabaseMessageRepository

Implements IMessageRepository using Supabase (PostgreSQL).
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from supabase import AsyncClient

from src.domain.entities.message import Message
from src.domain.repositories.message_repository import IMessageRepository
from src.domain.value_objects.message_role import MessageRole

_TABLE = "messages"


class SupabaseMessageRepository(IMessageRepository):

    def __init__(self, client: AsyncClient) -> None:
        self._client = client

    async def save(self, message: Message) -> None:
        row = self._to_row(message)
        try:
            await (
                self._client.table(_TABLE)
                .upsert(row, on_conflict="id")
                .execute()
            )
        except Exception as exc:
            raise RuntimeError(f"Failed to save message '{message.id}': {exc}") from exc

    async def get_by_id(self, message_id: str) -> Message | None:
        try:
            result = (
                await self._client.table(_TABLE)
                .select("*")
                .eq("id", message_id)
                .limit(1)
                .execute()
            )
        except Exception as exc:
            raise RuntimeError(f"Failed to fetch message '{message_id}': {exc}") from exc

        if not result.data:
            return None
        return self._to_entity(result.data[0])

    async def list_by_session(
        self, session_id: str, *, limit: int = 100, offset: int = 0
    ) -> list[Message]:
        try:
            result = (
                await self._client.table(_TABLE)
                .select("*")
                .eq("session_id", session_id)
                .order("created_at", desc=False)
                .range(offset, offset + limit - 1)
                .execute()
            )
        except Exception as exc:
            raise RuntimeError(
                f"Failed to list messages for session '{session_id}': {exc}"
            ) from exc
        return [self._to_entity(r) for r in result.data]

    async def delete_by_session(self, session_id: str) -> None:
        try:
            await (
                self._client.table(_TABLE)
                .delete()
                .eq("session_id", session_id)
                .execute()
            )
        except Exception as exc:
            raise RuntimeError(
                f"Failed to delete messages for session '{session_id}': {exc}"
            ) from exc

    # ── Mapping ───────────────────────────────────────────────────────────

    @staticmethod
    def _to_row(message: Message) -> dict[str, Any]:
        return {
            "id": message.id,
            "session_id": message.session_id,
            "role": message.role.value,
            "content": message.content,
            "audio_url": message.audio_url,
            "created_at": message.created_at.isoformat(),
        }

    @staticmethod
    def _to_entity(row: dict[str, Any]) -> Message:
        return Message(
            message_id=row["id"],
            session_id=row["session_id"],
            role=MessageRole(row["role"]),
            content=row["content"],
            audio_url=row.get("audio_url"),
            created_at=datetime.fromisoformat(row["created_at"]).replace(
                tzinfo=timezone.utc
            ),
        )
