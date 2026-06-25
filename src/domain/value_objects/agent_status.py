"""
AgentStatus value object.

Immutable enum-backed value object representing the lifecycle state of an Agent.
"""
from __future__ import annotations

from enum import Enum


class AgentStatus(str, Enum):
    """Possible states an Agent can be in."""

    IDLE = "idle"
    ACTIVE = "active"
    BUSY = "busy"
    OFFLINE = "offline"
    SUSPENDED = "suspended"

    # ── Transition guards ──────────────────────────────────────────────────

    def can_activate(self) -> bool:
        return self in (AgentStatus.IDLE, AgentStatus.OFFLINE)

    def can_suspend(self) -> bool:
        return self in (AgentStatus.IDLE, AgentStatus.ACTIVE, AgentStatus.BUSY)

    def can_go_offline(self) -> bool:
        return self in (AgentStatus.IDLE, AgentStatus.ACTIVE)

    def can_go_busy(self) -> bool:
        return self == AgentStatus.ACTIVE

    def is_available(self) -> bool:
        """Whether this agent can accept new sessions."""
        return self == AgentStatus.ACTIVE
