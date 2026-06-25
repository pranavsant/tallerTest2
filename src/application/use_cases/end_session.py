"""
EndSessionUseCase

Ends an active session and frees the associated agent.
"""
from __future__ import annotations

from src.application.dtos.session_dtos import EndSessionInputDTO, SessionOutputDTO
from src.application.mappers.session_mapper import SessionMapper
from src.application.ports.realtime_publisher import IRealtimePublisher
from src.domain.exceptions import AgentNotFoundError, SessionNotFoundError
from src.domain.repositories.agent_repository import IAgentRepository
from src.domain.repositories.session_repository import ISessionRepository
from src.domain.services.session_orchestrator import SessionOrchestrator


class EndSessionUseCase:
    def __init__(
        self,
        session_repository: ISessionRepository,
        agent_repository: IAgentRepository,
        orchestrator: SessionOrchestrator,
        publisher: IRealtimePublisher,
    ) -> None:
        self._sessions = session_repository
        self._agents = agent_repository
        self._orchestrator = orchestrator
        self._publisher = publisher

    async def execute(self, dto: EndSessionInputDTO) -> SessionOutputDTO:
        session = await self._sessions.get_by_id(dto.session_id)
        if session is None:
            raise SessionNotFoundError(f"Session '{dto.session_id}' not found")

        agent = await self._agents.get_by_id(session.agent_id)
        if agent is None:
            raise AgentNotFoundError(f"Agent '{session.agent_id}' not found")

        self._orchestrator.end_session(agent, session)

        await self._sessions.save(session)
        await self._agents.save(agent)

        await self._publisher.publish(
            channel=f"session:{session.id}",
            event="session.ended",
            payload={
                "session_id": session.id,
                "duration_seconds": session.duration_seconds(),
            },
        )

        return SessionMapper.to_output_dto(session)
