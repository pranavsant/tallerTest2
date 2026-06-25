"""
SupabaseAgentRepository

Implements IAgentRepository using Supabase (PostgreSQL).
Maps DB rows ↔ Agent domain entities.
Infrastructure errors are caught and re-raised as domain exceptions.
"""
from __future__ import annotations

from typing import Any

from supabase import AsyncClient

from src.domain.entities.agent import Agent
from src.domain.exceptions import AgentNotFoundError
from src.domain.repositories.agent_repository import IAgentRepository
from src.domain.value_objects.agent_status import AgentStatus
from src.domain.value_objects.voice_settings import VoiceSettings

_TABLE = "agents"


class SupabaseAgentRepository(IAgentRepository):
    """Supabase-backed implementation of IAgentRepository."""

    def __init__(self, client: AsyncClient) -> None:
        self._client = client

    # ── IAgentRepository implementation ───────────────────────────────────

    async def save(self, agent: Agent) -> None:
        row = self._to_row(agent)
        try:
            await (
                self._client.table(_TABLE)
                .upsert(row, on_conflict="id")
                .execute()
            )
        except Exception as exc:
            raise RuntimeError(f"Failed to save agent '{agent.id}': {exc}") from exc

    async def get_by_id(self, agent_id: str) -> Agent | None:
        try:
            result = (
                await self._client.table(_TABLE)
                .select("*")
                .eq("id", agent_id)
                .limit(1)
                .execute()
            )
        except Exception as exc:
            raise RuntimeError(f"Failed to fetch agent '{agent_id}': {exc}") from exc

        if not result.data:
            return None
        return self._to_entity(result.data[0])

    async def list_by_status(
        self,
        status: AgentStatus,
        *,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Agent]:
        try:
            result = (
                await self._client.table(_TABLE)
                .select("*")
                .eq("status", status.value)
                .range(offset, offset + limit - 1)
                .execute()
            )
        except Exception as exc:
            raise RuntimeError(f"Failed to list agents by status: {exc}") from exc

        return [self._to_entity(row) for row in result.data]

    async def list_all(self, *, limit: int = 50, offset: int = 0) -> list[Agent]:
        try:
            result = (
                await self._client.table(_TABLE)
                .select("*")
                .range(offset, offset + limit - 1)
                .execute()
            )
        except Exception as exc:
            raise RuntimeError(f"Failed to list agents: {exc}") from exc

        return [self._to_entity(row) for row in result.data]

    async def delete(self, agent_id: str) -> None:
        if not await self.exists(agent_id):
            raise AgentNotFoundError(f"Agent '{agent_id}' not found")
        try:
            await self._client.table(_TABLE).delete().eq("id", agent_id).execute()
        except Exception as exc:
            raise RuntimeError(f"Failed to delete agent '{agent_id}': {exc}") from exc

    async def exists(self, agent_id: str) -> bool:
        try:
            result = (
                await self._client.table(_TABLE)
                .select("id")
                .eq("id", agent_id)
                .limit(1)
                .execute()
            )
        except Exception as exc:
            raise RuntimeError(f"Failed to check agent existence: {exc}") from exc

        return len(result.data) > 0

    # ── Private mapping helpers ────────────────────────────────────────────

    @staticmethod
    def _to_row(agent: Agent) -> dict[str, Any]:
        return {
            "id": agent.id,
            "name": agent.name,
            "system_prompt": agent.system_prompt,
            "status": agent.status.value,
            "voice_id": agent.voice_settings.voice_id,
            "model_id": agent.voice_settings.model_id,
            "stability": agent.voice_settings.stability,
            "similarity_boost": agent.voice_settings.similarity_boost,
            "style": agent.voice_settings.style,
            "use_speaker_boost": agent.voice_settings.use_speaker_boost,
            "created_at": agent.created_at.isoformat(),
            "updated_at": agent.updated_at.isoformat(),
        }

    @staticmethod
    def _to_entity(row: dict[str, Any]) -> Agent:
        from datetime import datetime, timezone

        voice_settings = VoiceSettings(
            voice_id=row["voice_id"],
            model_id=row["model_id"],
            stability=float(row["stability"]),
            similarity_boost=float(row["similarity_boost"]),
            style=float(row.get("style", 0.0)),
            use_speaker_boost=bool(row.get("use_speaker_boost", True)),
        )
        return Agent(
            agent_id=row["id"],
            name=row["name"],
            system_prompt=row["system_prompt"],
            voice_settings=voice_settings,
            status=AgentStatus(row["status"]),
            created_at=datetime.fromisoformat(row["created_at"]).replace(
                tzinfo=timezone.utc
            ),
            updated_at=datetime.fromisoformat(row["updated_at"]).replace(
                tzinfo=timezone.utc
            ),
        )
