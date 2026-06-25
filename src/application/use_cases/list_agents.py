"""
ListAgentsUseCase

Returns a paginated list of agents with optional status filtering.
"""
from __future__ import annotations

from src.application.dtos.agent_dtos import AgentListOutputDTO, ListAgentsInputDTO
from src.application.mappers.agent_mapper import AgentMapper
from src.domain.repositories.agent_repository import IAgentRepository
from src.domain.value_objects.agent_status import AgentStatus


class ListAgentsUseCase:
    def __init__(self, agent_repository: IAgentRepository) -> None:
        self._repo = agent_repository

    async def execute(self, dto: ListAgentsInputDTO) -> AgentListOutputDTO:
        if dto.status_filter:
            agents = await self._repo.list_by_status(
                AgentStatus(dto.status_filter),
                limit=dto.limit,
                offset=dto.offset,
            )
        else:
            agents = await self._repo.list_all(limit=dto.limit, offset=dto.offset)

        return AgentListOutputDTO(
            agents=[AgentMapper.to_output_dto(a) for a in agents],
            total=len(agents),
            limit=dto.limit,
            offset=dto.offset,
        )
