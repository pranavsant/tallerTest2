"""
SessionMapper — converts Session entities to/from DTOs.
"""
from __future__ import annotations

from src.application.dtos.session_dtos import SessionOutputDTO
from src.domain.entities.session import Session


class SessionMapper:
    @staticmethod
    def to_output_dto(session: Session) -> SessionOutputDTO:
        return SessionOutputDTO(
            session_id=session.id,
            agent_id=session.agent_id,
            user_id=session.user_id,
            status=session.status.value,
            metadata=session.metadata,
            started_at=session.started_at,
            ended_at=session.ended_at,
            created_at=session.created_at,
            duration_seconds=session.duration_seconds(),
        )
