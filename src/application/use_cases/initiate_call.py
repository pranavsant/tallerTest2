"""
InitiateCallUseCase

Places an outbound call via the telephony service port.
"""
from __future__ import annotations

from src.application.dtos.call_dtos import CallOutputDTO, InitiateCallInputDTO
from src.application.mappers.call_mapper import CallMapper
from src.application.ports.telephony_service import ITelephonyService
from src.domain.entities.call import Call
from src.domain.exceptions import AgentNotFoundError
from src.domain.repositories.agent_repository import IAgentRepository
from src.domain.repositories.call_repository import ICallRepository
from src.domain.value_objects.phone_number import PhoneNumber


class InitiateCallUseCase:
    """
    Places an outbound Twilio call on behalf of an agent.

    Dependencies:
    - agent_repository:     IAgentRepository
    - call_repository:      ICallRepository
    - telephony_service:    ITelephonyService
    - from_phone_number:    str  (configured E.164 Twilio number, injected)
    - twiml_base_url:       str  (base URL for Twilio webhooks, injected)
    """

    def __init__(
        self,
        agent_repository: IAgentRepository,
        call_repository: ICallRepository,
        telephony_service: ITelephonyService,
        from_phone_number: str,
        twiml_base_url: str,
    ) -> None:
        self._agents = agent_repository
        self._calls = call_repository
        self._telephony = telephony_service
        self._from_number = PhoneNumber(from_phone_number)
        self._twiml_base_url = twiml_base_url.rstrip("/")

    async def execute(self, dto: InitiateCallInputDTO) -> CallOutputDTO:
        agent = await self._agents.get_by_id(dto.agent_id)
        if agent is None:
            raise AgentNotFoundError(f"Agent '{dto.agent_id}' not found")

        to_number = PhoneNumber(dto.to_phone_number)

        call = Call(
            agent_id=dto.agent_id,
            session_id=dto.session_id,
            to_number=to_number,
            from_number=self._from_number,
        )
        await self._calls.save(call)

        twiml_url = f"{self._twiml_base_url}/twiml/{call.id}"
        result = await self._telephony.initiate_call(
            to=str(to_number),
            from_=str(self._from_number),
            twiml_url=twiml_url,
        )

        call.assign_twilio_sid(result.twilio_call_sid)
        await self._calls.save(call)

        return CallMapper.to_output_dto(call)
