"""
SupabaseSessionRepository

Implements ISessionRepository using Supabase (PostgreSQL).
"""
from __future__ import annotations

from typing import Any
from datetime import datetime, timezone

from supabase import AsyncClient

from src.domain.entities.session import Session
from src.domain.repositories.session_repository import ISessionRepository
from src.domain.value_objects.session_status import SessionStatus

_TABLE = "sessions"


class SupabaseSessionRepository(ISessionRepository):

    def __init__(self, client: AsyncClient) -> None:
        self._client = client

    async def save(self, session: Session) -> None:
        row = self._to_row(session)
        try:
            await (
                self._client.table(_TABLE)
                .upsert(row, on_conflict="id")
                .execute()
            )
        except Exception as exc:
            raise RuntimeError(f"Failed to save session '{session.id}': {exc}") from exc

    async def get_by_id(self, session_id: str) -> Session | None:
        try:
            result = (
                await self._client.table(_TABLE)
                .select("*")
                .eq("id", session_id)
                .limit(1)
                .execute()
            )
        except Exception as exc:
            raise RuntimeError(f"Failed to fetch session '{session_id}': {exc}") from exc

        if not result.data:
            return None
        return self._to_entity(result.data[0])

    async def list_by_agent(
        self, agent_id: str, *, limit: int = 50, offset: int = 0
    ) -> list[Session]:
        try:
            result = (
                await self._client.table(_TABLE)
                .select("*")
                .eq("agent_id", agent_id)
                .range(offset, offset + limit - 1)
                .execute()
            )
        except Exception as exc:
            raise RuntimeError(f"Failed to list sessions for agent: {exc}") from exc
        return [self._to_entity(r) for r in result.data]

    async def list_by_user(
        self, user_id: str, *, limit: int = 50, offset: int = 0
    ) -> list[Session]:
        try:
            result = (
                await self._client.table(_TABLE)
                .select("*")
                .eq("user_id", user_id)
                .range(offset, offset + limit - 1)
                .execute()
            )
        except Exception as exc:
            raise RuntimeError(f"Failed to list sessions for user: {exc}") from exc
        return [self._to_entity(r) for r in result.data]

    async def list_active(self) -> list[Session]:
        try:
            result = (
                await self._client.table(_TABLE)
                .select("*")
                .eq("status", SessionStatus.ACTIVE.value)
                .execute()
            )
        except Exception as exc:
            raise RuntimeError(f"Failed to list active sessions: {exc}") from exc
        return [self._to_entity(r) for r in result.data]

    async def update_status(self, session_id: str, status: SessionStatus) -> None:
        try:
            await (
                self._client.table(_TABLE)
                .update({"status": status.value})
                .eq("id", session_id)
                .execute()
            )
        except Exception as exc:
            raise RuntimeError(f"Failed to update session status: {exc}") from exc

    async def delete(self, session_id: str) -> None:
        try:
            await self._client.table(_TABLE).delete().eq("id", session_id).execute()
        except Exception as exc:
            raise RuntimeError(f"Failed to delete session '{session_id}': {exc}") from exc

    # ── Mapping ───────────────────────────────────────────────────────────

    @staticmethod
    def _to_row(session: Session) -> dict[str, Any]:
        return {
            "id": session.id,
            "agent_id": session.agent_id,
            "user_id": session.user_id,
            "status": session.status.value,
            "metadata": session.metadata,
            "started_at": session.started_at.isoformat() if session.started_at else None,
            "ended_at": session.ended_at.isoformat() if session.ended_at else None,
            "created_at": session.created_at.isoformat(),
        }

    @staticmethod
    def _to_entity(row: dict[str, Any]) -> Session:
        def _parse(val: str | None) -> datetime | None:
            if val is None:
                return None
            return datetime.fromisoformat(val).replace(tzinfo=timezone.utc)

        return Session(
            session_id=row["id"],
            agent_id=row["agent_id"],
            user_id=row["user_id"],
            status=SessionStatus(row["status"]),
            metadata=dict(row.get("metadata") or {}),
            started_at=_parse(row.get("started_at")),
            ended_at=_parse(row.get("ended_at")),
            created_at=_parse(row["created_at"]) or datetime.now(timezone.utc),
        )
