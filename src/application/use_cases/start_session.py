"""
StartSessionUseCase

Starts a new session between a user and an agent.
"""
from __future__ import annotations

from src.application.dtos.session_dtos import SessionOutputDTO, StartSessionInputDTO
from src.application.mappers.session_mapper import SessionMapper
from src.application.ports.realtime_publisher import IRealtimePublisher
from src.domain.entities.session import Session
from src.domain.exceptions import AgentNotFoundError
from src.domain.repositories.agent_repository import IAgentRepository
from src.domain.repositories.session_repository import ISessionRepository
from src.domain.services.session_orchestrator import SessionOrchestrator


class StartSessionUseCase:
    """
    Starts a monitored session between a user and an available agent.

    Dependencies:
    - agent_repository:   IAgentRepository
    - session_repository: ISessionRepository
    - orchestrator:       SessionOrchestrator (domain service)
    - publisher:          IRealtimePublisher
    """

    def __init__(
        self,
        agent_repository: IAgentRepository,
        session_repository: ISessionRepository,
        orchestrator: SessionOrchestrator,
        publisher: IRealtimePublisher,
    ) -> None:
        self._agents = agent_repository
        self._sessions = session_repository
        self._orchestrator = orchestrator
        self._publisher = publisher

    async def execute(self, dto: StartSessionInputDTO) -> SessionOutputDTO:
        agent = await self._agents.get_by_id(dto.agent_id)
        if agent is None:
            raise AgentNotFoundError(f"Agent '{dto.agent_id}' not found")

        session = Session(
            agent_id=dto.agent_id,
            user_id=dto.user_id,
            metadata=dto.metadata or {},
        )

        # Domain service enforces agent availability and starts both entities
        self._orchestrator.begin_session(agent, session)

        await self._sessions.save(session)
        await self._agents.save(agent)

        await self._publisher.publish(
            channel=f"session:{session.id}",
            event="session.started",
            payload={"session_id": session.id, "agent_id": agent.id},
        )

        return SessionMapper.to_output_dto(session)
