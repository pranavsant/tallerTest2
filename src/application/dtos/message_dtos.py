"""
Message DTOs — typed contracts for message-related use cases.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


# ── Inputs ────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class SendMessageInputDTO:
    session_id: str
    user_id: str
    content: str
    synthesise_voice: bool = False


@dataclass(frozen=True)
class ListMessagesInputDTO:
    session_id: str
    limit: int = 100
    offset: int = 0


# ── Outputs ───────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class MessageOutputDTO:
    message_id: str
    session_id: str
    role: str
    content: str
    audio_url: str | None
    created_at: datetime


@dataclass(frozen=True)
class MessageListOutputDTO:
    messages: list[MessageOutputDTO]
    total: int
