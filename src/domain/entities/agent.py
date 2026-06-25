"""
Agent entity.

An Agent is an AI persona that can participate in sessions and calls.
It protects its own invariants and controls its own state transitions.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from src.domain.exceptions import (
    InvalidAgentNameError,
)
from src.domain.value_objects.agent_status import AgentStatus
from src.domain.value_objects.voice_settings import VoiceSettings


class Agent:
    """
    Core Agent entity.

    Invariants enforced in constructor:
    - name must be 1–100 characters
    - system_prompt must not be empty
    """

    MAX_NAME_LENGTH = 100
    MAX_SYSTEM_PROMPT_LENGTH = 8000

    def __init__(
        self,
        *,
        agent_id: str | None = None,
        name: str,
        system_prompt: str,
        voice_settings: VoiceSettings,
        status: AgentStatus = AgentStatus.IDLE,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ) -> None:
        self._id = agent_id or str(uuid.uuid4())
        self._created_at = created_at or datetime.now(timezone.utc)
        self._updated_at = updated_at or datetime.now(timezone.utc)

        # Delegate validation to setters so they're reused on mutation
        self.name = name
        self.system_prompt = system_prompt
        self.voice_settings = voice_settings
        self._status = status

    # ── Identity ───────────────────────────────────────────────────────────

    @property
    def id(self) -> str:
        return self._id

    @property
    def created_at(self) -> datetime:
        return self._created_at

    @property
    def updated_at(self) -> datetime:
        return self._updated_at

    # ── Mutable attributes with validation ────────────────────────────────

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value: str) -> None:
        stripped = value.strip()
        if not stripped or len(stripped) > self.MAX_NAME_LENGTH:
            raise InvalidAgentNameError(
                f"Agent name must be 1–{self.MAX_NAME_LENGTH} characters, got '{value}'"
            )
        self._name = stripped
        self._touch()

    @property
    def system_prompt(self) -> str:
        return self._system_prompt

    @system_prompt.setter
    def system_prompt(self, value: str) -> None:
        if not value.strip():
            raise ValueError("Agent system_prompt must not be empty")
        if len(value) > self.MAX_SYSTEM_PROMPT_LENGTH:
            raise ValueError(
                f"system_prompt exceeds max length of {self.MAX_SYSTEM_PROMPT_LENGTH}"
            )
        self._system_prompt = value
        self._touch()

    @property
    def voice_settings(self) -> VoiceSettings:
        return self._voice_settings

    @voice_settings.setter
    def voice_settings(self, value: VoiceSettings) -> None:
        self._voice_settings = value
        self._touch()

    # ── Status transitions ────────────────────────────────────────────────

    @property
    def status(self) -> AgentStatus:
        return self._status

    def activate(self) -> None:
        if not self._status.can_activate():
            raise ValueError(
                f"Cannot activate agent in status '{self._status}'"
            )
        self._status = AgentStatus.ACTIVE
        self._touch()

    def suspend(self) -> None:
        if not self._status.can_suspend():
            raise ValueError(
                f"Cannot suspend agent in status '{self._status}'"
            )
        self._status = AgentStatus.SUSPENDED
        self._touch()

    def go_offline(self) -> None:
        if not self._status.can_go_offline():
            raise ValueError(
                f"Cannot take agent offline from status '{self._status}'"
            )
        self._status = AgentStatus.OFFLINE
        self._touch()

    def mark_busy(self) -> None:
        if not self._status.can_go_busy():
            raise ValueError(
                f"Cannot mark agent busy from status '{self._status}'"
            )
        self._status = AgentStatus.BUSY
        self._touch()

    def is_available(self) -> bool:
        return self._status.is_available()

    # ── Internals ─────────────────────────────────────────────────────────

    def _touch(self) -> None:
        self._updated_at = datetime.now(timezone.utc)

    def __repr__(self) -> str:
        return f"Agent(id={self._id!r}, name={self._name!r}, status={self._status})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Agent):
            return NotImplemented
        return self._id == other._id

    def __hash__(self) -> int:
        return hash(self._id)
