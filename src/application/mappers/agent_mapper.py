"""
AgentMapper — converts Agent entities to/from DTOs.
No I/O; pure data transformation.
"""
from __future__ import annotations

from src.application.dtos.agent_dtos import AgentOutputDTO
from src.domain.entities.agent import Agent


class AgentMapper:
    @staticmethod
    def to_output_dto(agent: Agent) -> AgentOutputDTO:
        return AgentOutputDTO(
            agent_id=agent.id,
            name=agent.name,
            system_prompt=agent.system_prompt,
            status=agent.status.value,
            voice_id=agent.voice_settings.voice_id,
            model_id=agent.voice_settings.model_id,
            stability=agent.voice_settings.stability,
            similarity_boost=agent.voice_settings.similarity_boost,
            created_at=agent.created_at,
            updated_at=agent.updated_at,
        )
