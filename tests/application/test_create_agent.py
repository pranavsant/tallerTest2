"""
Unit tests for CreateAgentUseCase.

Uses an in-memory repository stub — no Supabase, no network.
"""
from __future__ import annotations

import pytest

from src.application.dtos.agent_dtos import CreateAgentInputDTO
from src.application.use_cases.create_agent import CreateAgentUseCase
from src.domain.entities.agent import Agent
from src.domain.repositories.agent_repository import IAgentRepository
from src.domain.value_objects.agent_status import AgentStatus


class InMemoryAgentRepository(IAgentRepository):
    """Minimal in-memory stub for tests."""

    def __init__(self) -> None:
        self._store: dict[str, Agent] = {}

    async def save(self, agent: Agent) -> None:
        self._store[agent.id] = agent

    async def get_by_id(self, agent_id: str) -> Agent | None:
        return self._store.get(agent_id)

    async def list_by_status(self, status: AgentStatus, *, limit: int = 50, offset: int = 0) -> list[Agent]:
        return [a for a in self._store.values() if a.status == status]

    async def list_all(self, *, limit: int = 50, offset: int = 0) -> list[Agent]:
        return list(self._store.values())

    async def delete(self, agent_id: str) -> None:
        self._store.pop(agent_id, None)

    async def exists(self, agent_id: str) -> bool:
        return agent_id in self._store


@pytest.fixture()
def repo() -> InMemoryAgentRepository:
    return InMemoryAgentRepository()


@pytest.fixture()
def use_case(repo: InMemoryAgentRepository) -> CreateAgentUseCase:
    return CreateAgentUseCase(repo)


class TestCreateAgentUseCase:
    async def test_creates_agent_and_returns_dto(
        self, use_case: CreateAgentUseCase, repo: InMemoryAgentRepository
    ) -> None:
        dto = CreateAgentInputDTO(
            name="Aria",
            system_prompt="You are Aria, a helpful AI assistant.",
            voice_id="test-voice-id",
        )
        result = await use_case.execute(dto)

        assert result.name == "Aria"
        assert result.status == "idle"
        assert result.voice_id == "test-voice-id"
        assert await repo.exists(result.agent_id)

    async def test_persists_agent_in_repository(
        self, use_case: CreateAgentUseCase, repo: InMemoryAgentRepository
    ) -> None:
        dto = CreateAgentInputDTO(
            name="Bob",
            system_prompt="You are Bob.",
            voice_id="voice-bob",
        )
        result = await use_case.execute(dto)
        saved = await repo.get_by_id(result.agent_id)
        assert saved is not None
        assert saved.name == "Bob"

    async def test_raises_on_invalid_name(
        self, use_case: CreateAgentUseCase
    ) -> None:
        dto = CreateAgentInputDTO(
            name="",
            system_prompt="You are helpful.",
            voice_id="voice-id",
        )
        with pytest.raises(Exception):
            await use_case.execute(dto)
