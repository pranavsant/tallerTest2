"""
Session DTOs — typed contracts for session-related use cases.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


# ── Inputs ────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class StartSessionInputDTO:
    agent_id: str
    user_id: str
    metadata: dict[str, str] | None = None


@dataclass(frozen=True)
class EndSessionInputDTO:
    session_id: str
    user_id: str  # ownership check


@dataclass(frozen=True)
class GetSessionInputDTO:
    session_id: str


# ── Outputs ───────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class SessionOutputDTO:
    session_id: str
    agent_id: str
    user_id: str
    status: str
    metadata: dict[str, str]
    started_at: datetime | None
    ended_at: datetime | None
    created_at: datetime
    duration_seconds: float | None
