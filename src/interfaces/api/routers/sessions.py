"""
Sessions router — /sessions
"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from src.application.dtos.session_dtos import (
    EndSessionInputDTO,
    GetSessionInputDTO,
    SessionOutputDTO,
    StartSessionInputDTO,
)
from src.application.use_cases.end_session import EndSessionUseCase
from src.application.use_cases.start_session import StartSessionUseCase
from src.domain.value_objects.authenticated_user import AuthenticatedUser
from src.interfaces.api.container import (
    get_end_session_use_case,
    get_start_session_use_case,
)
from src.interfaces.api.core.dependencies import get_current_user

router = APIRouter()


# ── Schemas ───────────────────────────────────────────────────────────────────


class StartSessionRequest(BaseModel):
    agent_id: str = Field(..., min_length=1)
    metadata: dict[str, str] | None = None


class SessionResponse(BaseModel):
    session_id: str
    agent_id: str
    user_id: str
    status: str
    metadata: dict[str, str]
    started_at: str | None
    ended_at: str | None
    created_at: str
    duration_seconds: float | None

    @classmethod
    def from_dto(cls, dto: SessionOutputDTO) -> "SessionResponse":
        return cls(
            session_id=dto.session_id,
            agent_id=dto.agent_id,
            user_id=dto.user_id,
            status=dto.status,
            metadata=dto.metadata,
            started_at=dto.started_at.isoformat() if dto.started_at else None,
            ended_at=dto.ended_at.isoformat() if dto.ended_at else None,
            created_at=dto.created_at.isoformat(),
            duration_seconds=dto.duration_seconds,
        )


# ── Endpoints ─────────────────────────────────────────────────────────────────


@router.post("", response_model=SessionResponse, status_code=201)
async def start_session(
    body: StartSessionRequest,
    use_case: StartSessionUseCase = Depends(get_start_session_use_case),
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> SessionResponse:
    """Start a new session between a user and an agent."""
    dto = StartSessionInputDTO(
        agent_id=body.agent_id,
        user_id=current_user.user_id,
        metadata=body.metadata,
    )
    result = await use_case.execute(dto)
    return SessionResponse.from_dto(result)


@router.delete("/{session_id}", response_model=SessionResponse)
async def end_session(
    session_id: str,
    use_case: EndSessionUseCase = Depends(get_end_session_use_case),
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> SessionResponse:
    """End an active session."""
    dto = EndSessionInputDTO(session_id=session_id, user_id=current_user.user_id)
    result = await use_case.execute(dto)
    return SessionResponse.from_dto(result)
