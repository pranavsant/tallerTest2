"""
SupabaseCallRepository

Implements ICallRepository using Supabase (PostgreSQL).
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from supabase import AsyncClient

from src.domain.entities.call import Call, CallStatus
from src.domain.repositories.call_repository import ICallRepository
from src.domain.value_objects.phone_number import PhoneNumber

_TABLE = "calls"


class SupabaseCallRepository(ICallRepository):

    def __init__(self, client: AsyncClient) -> None:
        self._client = client

    async def save(self, call: Call) -> None:
        row = self._to_row(call)
        try:
            await (
                self._client.table(_TABLE)
                .upsert(row, on_conflict="id")
                .execute()
            )
        except Exception as exc:
            raise RuntimeError(f"Failed to save call '{call.id}': {exc}") from exc

    async def get_by_id(self, call_id: str) -> Call | None:
        try:
            result = (
                await self._client.table(_TABLE)
                .select("*")
                .eq("id", call_id)
                .limit(1)
                .execute()
            )
        except Exception as exc:
            raise RuntimeError(f"Failed to fetch call '{call_id}': {exc}") from exc
        if not result.data:
            return None
        return self._to_entity(result.data[0])

    async def get_by_twilio_sid(self, sid: str) -> Call | None:
        try:
            result = (
                await self._client.table(_TABLE)
                .select("*")
                .eq("twilio_call_sid", sid)
                .limit(1)
                .execute()
            )
        except Exception as exc:
            raise RuntimeError(f"Failed to fetch call by SID '{sid}': {exc}") from exc
        if not result.data:
            return None
        return self._to_entity(result.data[0])

    async def list_by_agent(
        self, agent_id: str, *, limit: int = 50, offset: int = 0
    ) -> list[Call]:
        try:
            result = (
                await self._client.table(_TABLE)
                .select("*")
                .eq("agent_id", agent_id)
                .range(offset, offset + limit - 1)
                .execute()
            )
        except Exception as exc:
            raise RuntimeError(f"Failed to list calls for agent: {exc}") from exc
        return [self._to_entity(r) for r in result.data]

    async def delete(self, call_id: str) -> None:
        try:
            await self._client.table(_TABLE).delete().eq("id", call_id).execute()
        except Exception as exc:
            raise RuntimeError(f"Failed to delete call '{call_id}': {exc}") from exc

    # ── Mapping ───────────────────────────────────────────────────────────

    @staticmethod
    def _to_row(call: Call) -> dict[str, Any]:
        def _iso(val: datetime | None) -> str | None:
            return val.isoformat() if val else None

        return {
            "id": call.id,
            "agent_id": call.agent_id,
            "session_id": call.session_id,
            "to_number": str(call.to_number),
            "from_number": str(call.from_number),
            "twilio_call_sid": call.twilio_call_sid,
            "status": call.status.value,
            "recording_url": call.recording_url,
            "started_at": _iso(call.started_at),
            "ended_at": _iso(call.ended_at),
            "created_at": _iso(call.created_at),
        }

    @staticmethod
    def _to_entity(row: dict[str, Any]) -> Call:
        def _parse(val: str | None) -> datetime | None:
            if val is None:
                return None
            return datetime.fromisoformat(val).replace(tzinfo=timezone.utc)

        return Call(
            call_id=row["id"],
            agent_id=row["agent_id"],
            session_id=row.get("session_id"),
            to_number=PhoneNumber(row["to_number"]),
            from_number=PhoneNumber(row["from_number"]),
            twilio_call_sid=row.get("twilio_call_sid"),
            status=CallStatus(row["status"]),
            recording_url=row.get("recording_url"),
            started_at=_parse(row.get("started_at")),
            ended_at=_parse(row.get("ended_at")),
            created_at=_parse(row["created_at"]) or datetime.now(timezone.utc),
        )
