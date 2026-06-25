"""
SendMessageUseCase

Handles an inbound user message within a session, optionally
synthesising a voice response via the voice service port.
"""
from __future__ import annotations

from src.application.dtos.message_dtos import MessageOutputDTO, SendMessageInputDTO
from src.application.mappers.message_mapper import MessageMapper
from src.application.ports.realtime_publisher import IRealtimePublisher
from src.application.ports.voice_service import IVoiceService
from src.domain.exceptions import AgentNotFoundError, SessionNotFoundError
from src.domain.repositories.agent_repository import IAgentRepository
from src.domain.repositories.message_repository import IMessageRepository
from src.domain.repositories.session_repository import ISessionRepository
from src.domain.services.session_orchestrator import SessionOrchestrator


class SendMessageUseCase:
    """
    Records a user message and generates an agent reply.

    Dependencies:
    - session_repository: ISessionRepository
    - message_repository: IMessageRepository
    - agent_repository:   IAgentRepository
    - orchestrator:       SessionOrchestrator
    - voice_service:      IVoiceService
    - publisher:          IRealtimePublisher
    """

    # Placeholder reply — a real implementation would call an LLM port here
    _PLACEHOLDER_REPLY = (
        "I have received your message and I am processing it. "
        "This is a placeholder response from Overseer AI."
    )

    def __init__(
        self,
        session_repository: ISessionRepository,
        message_repository: IMessageRepository,
        agent_repository: IAgentRepository,
        orchestrator: SessionOrchestrator,
        voice_service: IVoiceService,
        publisher: IRealtimePublisher,
    ) -> None:
        self._sessions = session_repository
        self._messages = message_repository
        self._agents = agent_repository
        self._orchestrator = orchestrator
        self._voice_service = voice_service
        self._publisher = publisher

    async def execute(self, dto: SendMessageInputDTO) -> MessageOutputDTO:
        session = await self._sessions.get_by_id(dto.session_id)
        if session is None:
            raise SessionNotFoundError(f"Session '{dto.session_id}' not found")

        agent = await self._agents.get_by_id(session.agent_id)
        if agent is None:
            raise AgentNotFoundError(f"Agent '{session.agent_id}' not found")

        # Domain service builds and validates the user message
        user_msg = self._orchestrator.build_user_message(session, dto.content)
        await self._messages.save(user_msg)

        # Build agent reply
        reply_content = self._PLACEHOLDER_REPLY
        audio_url: str | None = None

        if dto.synthesise_voice:
            audio_bytes = await self._voice_service.synthesise(
                text=reply_content,
                settings=agent.voice_settings,
            )
            # In production this would be uploaded and return a URL;
            # placeholder returns None here.
            _ = audio_bytes  # consumed by storage layer in a real flow

        agent_msg = self._orchestrator.build_agent_message(
            session, reply_content, audio_url=audio_url
        )
        await self._messages.save(agent_msg)

        # Broadcast to WebSocket subscribers
        await self._publisher.publish(
            channel=f"session:{session.id}",
            event="message.created",
            payload={
                "message_id": agent_msg.id,
                "role": agent_msg.role.value,
                "content": agent_msg.content,
                "audio_url": agent_msg.audio_url,
            },
        )

        return MessageMapper.to_output_dto(agent_msg)
