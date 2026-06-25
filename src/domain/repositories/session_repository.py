"""
ISessionRepository — domain interface for Session persistence.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from src.domain.entities.session import Session
from src.domain.value_objects.session_status import SessionStatus


class ISessionRepository(ABC):

    @abstractmethod
    async def save(self, session: Session) -> None:
        ...

    @abstractmethod
    async def get_by_id(self, session_id: str) -> Session | None:
        ...

    @abstractmethod
    async def list_by_agent(
        self,
        agent_id: str,
        *,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Session]:
        ...

    @abstractmethod
    async def list_by_user(
        self,
        user_id: str,
        *,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Session]:
        ...

    @abstractmethod
    async def list_active(self) -> list[Session]:
        """Return all sessions currently in ACTIVE status."""
        ...

    @abstractmethod
    async def update_status(self, session_id: str, status: SessionStatus) -> None:
        ...

    @abstractmethod
    async def delete(self, session_id: str) -> None:
        ...
