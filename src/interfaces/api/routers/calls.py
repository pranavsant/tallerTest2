"""
Calls router — /calls

Handles outbound Twilio calls and incoming Twilio webhooks.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Form, Response
from pydantic import BaseModel, Field

from src.application.dtos.call_dtos import CallOutputDTO, InitiateCallInputDTO
from src.application.use_cases.initiate_call import InitiateCallUseCase
from src.domain.value_objects.authenticated_user import AuthenticatedUser
from src.interfaces.api.container import get_initiate_call_use_case
from src.interfaces.api.core.dependencies import get_current_user

router = APIRouter()


class InitiateCallRequest(BaseModel):
    agent_id: str = Field(..., min_length=1)
    to_phone_number: str = Field(..., min_length=7)
    session_id: str | None = None


class CallResponse(BaseModel):
    call_id: str
    agent_id: str
    session_id: str | None
    to_number: str
    from_number: str
    twilio_call_sid: str | None
    status: str
    created_at: str

    @classmethod
    def from_dto(cls, dto: CallOutputDTO) -> "CallResponse":
        return cls(
            call_id=dto.call_id,
            agent_id=dto.agent_id,
            session_id=dto.session_id,
            to_number=dto.to_number,
            from_number=dto.from_number,
            twilio_call_sid=dto.twilio_call_sid,
            status=dto.status,
            created_at=dto.created_at.isoformat(),
        )


@router.post("", response_model=CallResponse, status_code=201)
async def initiate_call(
    body: InitiateCallRequest,
    use_case: InitiateCallUseCase = Depends(get_initiate_call_use_case),
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> CallResponse:
    """Initiate an outbound call via Twilio. Requires authentication."""
    dto = InitiateCallInputDTO(
        agent_id=body.agent_id,
        to_phone_number=body.to_phone_number,
        session_id=body.session_id,
    )
    result = await use_case.execute(dto)
    return CallResponse.from_dto(result)


@router.post("/twiml/{call_id}", include_in_schema=False)
async def twiml_webhook(call_id: str) -> Response:
    """
    Twilio webhook — returns TwiML instructions for the call.
    This endpoint is called by Twilio when the call connects.
    """
    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Say voice="alice">
    Hello, this is Overseer AI. Your call reference is {call_id}.
    Please hold while I connect you with your AI agent.
  </Say>
  <Pause length="1"/>
</Response>"""
    return Response(content=twiml, media_type="application/xml")


@router.post("/webhook/status", include_in_schema=False)
async def call_status_webhook(
    CallSid: str = Form(...),
    CallStatus: str = Form(...),
    RecordingUrl: str | None = Form(default=None),
) -> Response:
    """
    Twilio status callback — update call status in the database.
    In production, resolve and execute UpdateCallStatusUseCase here.
    """
    # TODO: inject UpdateCallStatusUseCase and execute it
    return Response(status_code=204)
