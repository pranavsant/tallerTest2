"""
Message entity.

A Message is a single turn within a Session conversation.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from src.domain.exceptions import EmptyMessageContentError, MessageTooLongError
from src.domain.value_objects.message_role import MessageRole


class Message:
    """
    A single conversational turn within a Session.

    Invariants:
    - content must be non-empty
    - content must not exceed MAX_CONTENT_LENGTH
    """

    MAX_CONTENT_LENGTH = 32_000  # ~8k tokens at 4 chars/token

    def __init__(
        self,
        *,
        message_id: str | None = None,
        session_id: str,
        role: MessageRole,
        content: str,
        audio_url: str | None = None,
        created_at: datetime | None = None,
    ) -> None:
        self._id = message_id or str(uuid.uuid4())
        self._session_id = session_id
        self._role = role
        self._audio_url = audio_url
        self._created_at = created_at or datetime.now(timezone.utc)

        # Validate content through property
        self.content = content

    # ── Identity ───────────────────────────────────────────────────────────

    @property
    def id(self) -> str:
        return self._id

    @property
    def session_id(self) -> str:
        return self._session_id

    @property
    def role(self) -> MessageRole:
        return self._role

    @property
    def audio_url(self) -> str | None:
        return self._audio_url

    @property
    def created_at(self) -> datetime:
        return self._created_at

    # ── Content ────────────────────────────────────────────────────────────

    @property
    def content(self) -> str:
        return self._content

    @content.setter
    def content(self, value: str) -> None:
        if not value or not value.strip():
            raise EmptyMessageContentError("Message content must not be empty")
        if len(value) > self.MAX_CONTENT_LENGTH:
            raise MessageTooLongError(
                f"Message content exceeds {self.MAX_CONTENT_LENGTH} characters"
            )
        self._content = value

    def attach_audio(self, audio_url: str) -> None:
        """Attach a synthesised audio URL to this message (post-creation)."""
        if not audio_url.startswith("http"):
            raise ValueError("audio_url must be a valid HTTP URL")
        self._audio_url = audio_url

    def __repr__(self) -> str:
        preview = self._content[:40].replace("\n", " ")
        return f"Message(id={self._id!r}, role={self._role}, content={preview!r}...)"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Message):
            return NotImplemented
        return self._id == other._id

    def __hash__(self) -> int:
        return hash(self._id)
