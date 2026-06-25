"""
SessionStatus value object.

Represents the lifecycle state of a monitoring session.
"""
from __future__ import annotations

from enum import Enum


class SessionStatus(str, Enum):
    PENDING = "pending"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"

    def is_terminal(self) -> bool:
        return self in (SessionStatus.COMPLETED, SessionStatus.FAILED)

    def can_receive_messages(self) -> bool:
        return self == SessionStatus.ACTIVE
