"""
CallMapper — converts Call entities to/from DTOs.
"""
from __future__ import annotations

from src.application.dtos.call_dtos import CallOutputDTO
from src.domain.entities.call import Call


class CallMapper:
    @staticmethod
    def to_output_dto(call: Call) -> CallOutputDTO:
        return CallOutputDTO(
            call_id=call.id,
            agent_id=call.agent_id,
            session_id=call.session_id,
            to_number=str(call.to_number),
            from_number=str(call.from_number),
            twilio_call_sid=call.twilio_call_sid,
            status=call.status.value,
            recording_url=call.recording_url,
            started_at=call.started_at,
            ended_at=call.ended_at,
            created_at=call.created_at,
            duration_seconds=call.duration_seconds(),
        )
