"""
MessageMapper — converts Message entities to/from DTOs.
"""
from __future__ import annotations

from src.application.dtos.message_dtos import MessageOutputDTO
from src.domain.entities.message import Message


class MessageMapper:
    @staticmethod
    def to_output_dto(message: Message) -> MessageOutputDTO:
        return MessageOutputDTO(
            message_id=message.id,
            session_id=message.session_id,
            role=message.role.value,
            content=message.content,
            audio_url=message.audio_url,
            created_at=message.created_at,
        )
