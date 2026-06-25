"""
Messages router — /messages
"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from src.application.dtos.message_dtos import MessageOutputDTO, SendMessageInputDTO
from src.application.use_cases.send_message import SendMessageUseCase
from src.interfaces.api.container import get_send_message_use_case

router = APIRouter()


class SendMessageRequest(BaseModel):
    session_id: str = Field(..., min_length=1)
    user_id: str = Field(..., min_length=1)
    content: str = Field(..., min_length=1)
    synthesise_voice: bool = False


class MessageResponse(BaseModel):
    message_id: str
    session_id: str
    role: str
    content: str
    audio_url: str | None
    created_at: str

    @classmethod
    def from_dto(cls, dto: MessageOutputDTO) -> "MessageResponse":
        return cls(
            message_id=dto.message_id,
            session_id=dto.session_id,
            role=dto.role,
            content=dto.content,
            audio_url=dto.audio_url,
            created_at=dto.created_at.isoformat(),
        )


@router.post("", response_model=MessageResponse, status_code=201)
async def send_message(
    body: SendMessageRequest,
    use_case: SendMessageUseCase = Depends(get_send_message_use_case),
) -> MessageResponse:
    """Send a message within an active session and receive an agent reply."""
    dto = SendMessageInputDTO(
        session_id=body.session_id,
        user_id=body.user_id,
        content=body.content,
        synthesise_voice=body.synthesise_voice,
    )
    result = await use_case.execute(dto)
    return MessageResponse.from_dto(result)
