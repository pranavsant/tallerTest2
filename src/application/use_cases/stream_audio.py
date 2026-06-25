"""
StreamAudioUseCase

Synthesises speech from text and streams the audio bytes back to the caller.
Used by the WebSocket handler for realtime voice streaming.
"""
from __future__ import annotations

from dataclasses import dataclass

from src.application.ports.voice_service import IVoiceService
from src.domain.exceptions import AgentNotFoundError
from src.domain.repositories.agent_repository import IAgentRepository


@dataclass(frozen=True)
class StreamAudioInputDTO:
    agent_id: str
    text: str


@dataclass(frozen=True)
class StreamAudioOutputDTO:
    audio_bytes: bytes
    voice_id: str
    model_id: str


class StreamAudioUseCase:
    """
    Converts text to audio using the agent's configured voice settings.

    Dependencies:
    - agent_repository: IAgentRepository
    - voice_service:    IVoiceService
    """

    def __init__(
        self,
        agent_repository: IAgentRepository,
        voice_service: IVoiceService,
    ) -> None:
        self._agents = agent_repository
        self._voice_service = voice_service

    async def execute(self, dto: StreamAudioInputDTO) -> StreamAudioOutputDTO:
        agent = await self._agents.get_by_id(dto.agent_id)
        if agent is None:
            raise AgentNotFoundError(f"Agent '{dto.agent_id}' not found")

        audio_bytes = await self._voice_service.synthesise(
            text=dto.text,
            settings=agent.voice_settings,
        )

        return StreamAudioOutputDTO(
            audio_bytes=audio_bytes,
            voice_id=agent.voice_settings.voice_id,
            model_id=agent.voice_settings.model_id,
        )
