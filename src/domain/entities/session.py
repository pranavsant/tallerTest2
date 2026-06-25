"""
Session entity.

A Session represents a live interaction between a user and an Agent.
It owns the lifecycle and guards transitions between states.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from src.domain.exceptions import (
    SessionAlreadyActiveError,
    SessionNotActiveError,
)
from src.domain.value_objects.session_status import SessionStatus


class Session:
    """
    Session entity — a bounded conversation or call between a user and agent.

    Invariants:
    - started_at is set only when transitioning to ACTIVE
    - ended_at is set only when transitioning to a terminal state
    - Messages can only be added to an ACTIVE session
    """

    def __init__(
        self,
        *,
        session_id: str | None = None,
        agent_id: str,
        user_id: str,
        status: SessionStatus = SessionStatus.PENDING,
        metadata: dict[str, str] | None = None,
        started_at: datetime | None = None,
        ended_at: datetime | None = None,
        created_at: datetime | None = None,
    ) -> None:
        self._id = session_id or str(uuid.uuid4())
        self._agent_id = agent_id
        self._user_id = user_id
        self._status = status
        self._metadata: dict[str, str] = metadata or {}
        self._started_at = started_at
        self._ended_at = ended_at
        self._created_at = created_at or datetime.now(timezone.utc)

    # ── Identity ───────────────────────────────────────────────────────────

    @property
    def id(self) -> str:
        return self._id

    @property
    def agent_id(self) -> str:
        return self._agent_id

    @property
    def user_id(self) -> str:
        return self._user_id

    @property
    def status(self) -> SessionStatus:
        return self._status

    @property
    def metadata(self) -> dict[str, str]:
        return dict(self._metadata)

    @property
    def started_at(self) -> datetime | None:
        return self._started_at

    @property
    def ended_at(self) -> datetime | None:
        return self._ended_at

    @property
    def created_at(self) -> datetime:
        return self._created_at

    # ── State transitions ─────────────────────────────────────────────────

    def start(self) -> None:
        if self._status == SessionStatus.ACTIVE:
            raise SessionAlreadyActiveError(
                f"Session '{self._id}' is already active"
            )
        if self._status.is_terminal():
            raise ValueError(
                f"Cannot start a terminal session (status={self._status})"
            )
        self._status = SessionStatus.ACTIVE
        self._started_at = datetime.now(timezone.utc)

    def pause(self) -> None:
        if self._status != SessionStatus.ACTIVE:
            raise SessionNotActiveError(
                f"Session '{self._id}' must be ACTIVE to pause (current: {self._status})"
            )
        self._status = SessionStatus.PAUSED

    def resume(self) -> None:
        if self._status != SessionStatus.PAUSED:
            raise ValueError(
                f"Session '{self._id}' must be PAUSED to resume (current: {self._status})"
            )
        self._status = SessionStatus.ACTIVE

    def complete(self) -> None:
        if self._status.is_terminal():
            return  # idempotent
        self._status = SessionStatus.COMPLETED
        self._ended_at = datetime.now(timezone.utc)

    def fail(self, reason: str | None = None) -> None:
        if self._status.is_terminal():
            return
        self._status = SessionStatus.FAILED
        self._ended_at = datetime.now(timezone.utc)
        if reason:
            self._metadata["failure_reason"] = reason

    def assert_active(self) -> None:
        if not self._status.can_receive_messages():
            raise SessionNotActiveError(
                f"Session '{self._id}' is not active (status={self._status})"
            )

    # ── Duration ──────────────────────────────────────────────────────────

    def duration_seconds(self) -> float | None:
        if self._started_at is None:
            return None
        end = self._ended_at or datetime.now(timezone.utc)
        return (end - self._started_at).total_seconds()

    def __repr__(self) -> str:
        return f"Session(id={self._id!r}, agent={self._agent_id!r}, status={self._status})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Session):
            return NotImplemented
        return self._id == other._id

    def __hash__(self) -> int:
        return hash(self._id)
