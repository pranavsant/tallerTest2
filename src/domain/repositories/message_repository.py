"""
IMessageRepository — domain interface for Message persistence.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from src.domain.entities.message import Message


class IMessageRepository(ABC):

    @abstractmethod
    async def save(self, message: Message) -> None:
        ...

    @abstractmethod
    async def get_by_id(self, message_id: str) -> Message | None:
        ...

    @abstractmethod
    async def list_by_session(
        self,
        session_id: str,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Message]:
        """Return messages for a session in chronological order."""
        ...

    @abstractmethod
    async def delete_by_session(self, session_id: str) -> None:
        """Remove all messages belonging to a session."""
        ...
