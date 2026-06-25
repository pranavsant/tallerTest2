"""
Agent DTOs — typed contracts for agent-related use cases.
Pure dataclasses; no domain or infrastructure imports.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


# ── Inputs ────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class CreateAgentInputDTO:
    name: str
    system_prompt: str
    voice_id: str
    model_id: str = "eleven_turbo_v2"
    stability: float = 0.5
    similarity_boost: float = 0.75


@dataclass(frozen=True)
class UpdateAgentInputDTO:
    agent_id: str
    name: str | None = None
    system_prompt: str | None = None
    voice_id: str | None = None
    stability: float | None = None
    similarity_boost: float | None = None


@dataclass(frozen=True)
class GetAgentInputDTO:
    agent_id: str


@dataclass(frozen=True)
class ListAgentsInputDTO:
    status_filter: str | None = None
    limit: int = 50
    offset: int = 0


# ── Outputs ───────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class AgentOutputDTO:
    agent_id: str
    name: str
    system_prompt: str
    status: str
    voice_id: str
    model_id: str
    stability: float
    similarity_boost: float
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class AgentListOutputDTO:
    agents: list[AgentOutputDTO]
    total: int
    limit: int
    offset: int
