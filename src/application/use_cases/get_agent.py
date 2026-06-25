"""
GetAgentUseCase

Retrieves a single Agent by ID.
"""
from __future__ import annotations

from src.application.dtos.agent_dtos import AgentOutputDTO, GetAgentInputDTO
from src.application.mappers.agent_mapper import AgentMapper
from src.domain.exceptions import AgentNotFoundError
from src.domain.repositories.agent_repository import IAgentRepository


class GetAgentUseCase:
    def __init__(self, agent_repository: IAgentRepository) -> None:
        self._repo = agent_repository

    async def execute(self, dto: GetAgentInputDTO) -> AgentOutputDTO:
        agent = await self._repo.get_by_id(dto.agent_id)
        if agent is None:
            raise AgentNotFoundError(f"Agent '{dto.agent_id}' not found")
        return AgentMapper.to_output_dto(agent)
