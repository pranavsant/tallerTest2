"""
CreateAgentUseCase

Creates a new Agent with the given configuration and persists it.
"""
from __future__ import annotations

from src.application.dtos.agent_dtos import AgentOutputDTO, CreateAgentInputDTO
from src.application.mappers.agent_mapper import AgentMapper
from src.domain.entities.agent import Agent
from src.domain.repositories.agent_repository import IAgentRepository
from src.domain.value_objects.voice_settings import VoiceSettings


class CreateAgentUseCase:
    """
    Creates a new Agent.

    Dependencies injected via constructor:
    - agent_repository: IAgentRepository
    """

    def __init__(self, agent_repository: IAgentRepository) -> None:
        self._repo = agent_repository

    async def execute(self, dto: CreateAgentInputDTO) -> AgentOutputDTO:
        """
        Execute the use case.

        Args:
            dto: Validated input data from the interface layer.

        Returns:
            AgentOutputDTO representing the newly created agent.

        Raises:
            InvalidAgentNameError: if the name is invalid (enforced by entity).
            ValueError: if voice settings are out of range.
        """
        voice_settings = VoiceSettings(
            voice_id=dto.voice_id,
            model_id=dto.model_id,
            stability=dto.stability,
            similarity_boost=dto.similarity_boost,
        )

        agent = Agent(
            name=dto.name,
            system_prompt=dto.system_prompt,
            voice_settings=voice_settings,
        )

        await self._repo.save(agent)

        return AgentMapper.to_output_dto(agent)
