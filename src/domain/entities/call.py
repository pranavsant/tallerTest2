"""
Call entity.

A Call represents a Twilio telephony call managed by an Agent.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum

from src.domain.value_objects.phone_number import PhoneNumber


class CallStatus(str, Enum):
    QUEUED = "queued"
    RINGING = "ringing"
    IN_PROGRESS = "in-progress"
    COMPLETED = "completed"
    FAILED = "failed"
    NO_ANSWER = "no-answer"
    BUSY = "busy"
    CANCELED = "canceled"

    def is_terminal(self) -> bool:
        return self in (
            CallStatus.COMPLETED,
            CallStatus.FAILED,
            CallStatus.NO_ANSWER,
            CallStatus.BUSY,
            CallStatus.CANCELED,
        )


class Call:
    """
    Telephony call entity managed through Twilio.

    Invariants:
    - twilio_call_sid is immutable once set
    - ended_at can only be set once the call reaches a terminal status
    """

    def __init__(
        self,
        *,
        call_id: str | None = None,
        agent_id: str,
        session_id: str | None = None,
        to_number: PhoneNumber,
        from_number: PhoneNumber,
        twilio_call_sid: str | None = None,
        status: CallStatus = CallStatus.QUEUED,
        recording_url: str | None = None,
        started_at: datetime | None = None,
        ended_at: datetime | None = None,
        created_at: datetime | None = None,
    ) -> None:
        self._id = call_id or str(uuid.uuid4())
        self._agent_id = agent_id
        self._session_id = session_id
        self._to_number = to_number
        self._from_number = from_number
        self._twilio_call_sid = twilio_call_sid
        self._status = status
        self._recording_url = recording_url
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
    def session_id(self) -> str | None:
        return self._session_id

    @property
    def to_number(self) -> PhoneNumber:
        return self._to_number

    @property
    def from_number(self) -> PhoneNumber:
        return self._from_number

    @property
    def twilio_call_sid(self) -> str | None:
        return self._twilio_call_sid

    @property
    def status(self) -> CallStatus:
        return self._status

    @property
    def recording_url(self) -> str | None:
        return self._recording_url

    @property
    def started_at(self) -> datetime | None:
        return self._started_at

    @property
    def ended_at(self) -> datetime | None:
        return self._ended_at

    @property
    def created_at(self) -> datetime:
        return self._created_at

    # ── Transitions ────────────────────────────────────────────────────────

    def assign_twilio_sid(self, sid: str) -> None:
        if self._twilio_call_sid is not None:
            raise ValueError("twilio_call_sid is already set and immutable")
        self._twilio_call_sid = sid

    def mark_in_progress(self) -> None:
        if self._status.is_terminal():
            raise ValueError(f"Cannot progress a terminal call (status={self._status})")
        self._status = CallStatus.IN_PROGRESS
        self._started_at = self._started_at or datetime.now(timezone.utc)

    def complete(self, recording_url: str | None = None) -> None:
        self._status = CallStatus.COMPLETED
        self._ended_at = datetime.now(timezone.utc)
        if recording_url:
            self._recording_url = recording_url

    def fail(self) -> None:
        self._status = CallStatus.FAILED
        self._ended_at = datetime.now(timezone.utc)

    def duration_seconds(self) -> float | None:
        if self._started_at is None:
            return None
        end = self._ended_at or datetime.now(timezone.utc)
        return (end - self._started_at).total_seconds()

    def __repr__(self) -> str:
        return (
            f"Call(id={self._id!r}, to={self._to_number}, status={self._status})"
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Call):
            return NotImplemented
        return self._id == other._id

    def __hash__(self) -> int:
        return hash(self._id)
