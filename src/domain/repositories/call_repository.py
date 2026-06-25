"""
ICallRepository — domain interface for Call persistence.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from src.domain.entities.call import Call


class ICallRepository(ABC):

    @abstractmethod
    async def save(self, call: Call) -> None:
        ...

    @abstractmethod
    async def get_by_id(self, call_id: str) -> Call | None:
        ...

    @abstractmethod
    async def get_by_twilio_sid(self, sid: str) -> Call | None:
        ...

    @abstractmethod
    async def list_by_agent(
        self,
        agent_id: str,
        *,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Call]:
        ...

    @abstractmethod
    async def delete(self, call_id: str) -> None:
        ...
