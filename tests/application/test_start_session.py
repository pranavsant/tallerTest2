"""
Unit tests for StartSessionUseCase.
"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.application.dtos.session_dtos import StartSessionInputDTO
from src.application.use_cases.start_session import StartSessionUseCase
from src.domain.entities.agent import Agent
from src.domain.entities.session import Session
from src.domain.exceptions import AgentNotFoundError
from src.domain.repositories.agent_repository import IAgentRepository
from src.domain.repositories.session_repository import ISessionRepository
from src.domain.services.session_orchestrator import SessionOrchestrator
from src.domain.value_objects.agent_status import AgentStatus
from src.domain.value_objects.session_status import SessionStatus
from src.domain.value_objects.voice_settings import VoiceSettings


def _make_active_agent(agent_id: str = "agent-1") -> Agent:
    agent = Agent(
        agent_id=agent_id,
        name="Test Agent",
        system_prompt="You are helpful.",
        voice_settings=VoiceSettings(voice_id="voice-1"),
    )
    agent.activate()
    return agent


class TestStartSessionUseCase:
    @pytest.fixture()
    def active_agent(self) -> Agent:
        return _make_active_agent()

    @pytest.fixture()
    def agent_repo(self, active_agent: Agent) -> IAgentRepository:
        repo = AsyncMock(spec=IAgentRepository)
        repo.get_by_id.return_value = active_agent
        return repo

    @pytest.fixture()
    def session_repo(self) -> ISessionRepository:
        repo = AsyncMock(spec=ISessionRepository)
        return repo

    @pytest.fixture()
    def publisher(self) -> MagicMock:
        p = AsyncMock()
        return p

    @pytest.fixture()
    def use_case(
        self,
        agent_repo: IAgentRepository,
        session_repo: ISessionRepository,
        publisher: MagicMock,
    ) -> StartSessionUseCase:
        return StartSessionUseCase(
            agent_repository=agent_repo,
            session_repository=session_repo,
            orchestrator=SessionOrchestrator(),
            publisher=publisher,
        )

    async def test_starts_session_successfully(
        self, use_case: StartSessionUseCase
    ) -> None:
        dto = StartSessionInputDTO(agent_id="agent-1", user_id="user-1")
        result = await use_case.execute(dto)

        assert result.agent_id == "agent-1"
        assert result.user_id == "user-1"
        assert result.status == SessionStatus.ACTIVE.value

    async def test_raises_if_agent_not_found(
        self,
        session_repo: ISessionRepository,
        publisher: MagicMock,
    ) -> None:
        repo = AsyncMock(spec=IAgentRepository)
        repo.get_by_id.return_value = None
        uc = StartSessionUseCase(
            agent_repository=repo,
            session_repository=session_repo,
            orchestrator=SessionOrchestrator(),
            publisher=publisher,
        )
        with pytest.raises(AgentNotFoundError):
            await uc.execute(StartSessionInputDTO(agent_id="missing", user_id="u1"))

    async def test_publishes_session_started_event(
        self,
        use_case: StartSessionUseCase,
        publisher: MagicMock,
    ) -> None:
        dto = StartSessionInputDTO(agent_id="agent-1", user_id="user-1")
        result = await use_case.execute(dto)
        publisher.publish.assert_called_once()
        call_kwargs = publisher.publish.call_args
        assert call_kwargs.kwargs["event"] == "session.started"
