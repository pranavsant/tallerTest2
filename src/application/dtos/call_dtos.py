"""
Call DTOs — typed contracts for telephony use cases.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


# ── Inputs ────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class InitiateCallInputDTO:
    agent_id: str
    to_phone_number: str   # E.164 — validated when creating PhoneNumber VO
    session_id: str | None = None


@dataclass(frozen=True)
class UpdateCallStatusInputDTO:
    twilio_call_sid: str
    new_status: str
    recording_url: str | None = None


@dataclass(frozen=True)
class GetCallInputDTO:
    call_id: str


# ── Outputs ───────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class CallOutputDTO:
    call_id: str
    agent_id: str
    session_id: str | None
    to_number: str
    from_number: str
    twilio_call_sid: str | None
    status: str
    recording_url: str | None
    started_at: datetime | None
    ended_at: datetime | None
    created_at: datetime
    duration_seconds: float | None
