"""
IAgentRepository — domain interface for Agent persistence.

Implementations live in infrastructure/; this file contains zero I/O.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from src.domain.entities.agent import Agent
from src.domain.value_objects.agent_status import AgentStatus


class IAgentRepository(ABC):
    """Abstract repository contract for Agent persistence."""

    @abstractmethod
    async def save(self, agent: Agent) -> None:
        """Persist a new or updated Agent."""
        ...

    @abstractmethod
    async def get_by_id(self, agent_id: str) -> Agent | None:
        """Return an Agent by its ID, or None if not found."""
        ...

    @abstractmethod
    async def list_by_status(
        self,
        status: AgentStatus,
        *,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Agent]:
        """Return paginated agents filtered by status."""
        ...

    @abstractmethod
    async def list_all(
        self,
        *,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Agent]:
        """Return all agents (paginated)."""
        ...

    @abstractmethod
    async def delete(self, agent_id: str) -> None:
        """Hard-delete an Agent by ID."""
        ...

    @abstractmethod
    async def exists(self, agent_id: str) -> bool:
        """Return True if an Agent with the given ID exists."""
        ...
