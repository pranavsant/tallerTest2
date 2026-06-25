"""
Agents router — /agents

Thin controller: validate input → call use case → serialize output.
Zero business logic.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field

from src.application.dtos.agent_dtos import (
    AgentListOutputDTO,
    AgentOutputDTO,
    CreateAgentInputDTO,
    GetAgentInputDTO,
    ListAgentsInputDTO,
)
from src.application.use_cases.create_agent import CreateAgentUseCase
from src.application.use_cases.get_agent import GetAgentUseCase
from src.application.use_cases.list_agents import ListAgentsUseCase
from src.interfaces.api.container import (
    get_create_agent_use_case,
    get_get_agent_use_case,
    get_list_agents_use_case,
)

router = APIRouter()


# ── Request / response schemas ────────────────────────────────────────────────


class CreateAgentRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    system_prompt: str = Field(..., min_length=1)
    voice_id: str = Field(..., min_length=1)
    model_id: str = Field(default="eleven_turbo_v2")
    stability: float = Field(default=0.5, ge=0.0, le=1.0)
    similarity_boost: float = Field(default=0.75, ge=0.0, le=1.0)


class AgentResponse(BaseModel):
    agent_id: str
    name: str
    system_prompt: str
    status: str
    voice_id: str
    model_id: str
    stability: float
    similarity_boost: float
    created_at: str
    updated_at: str

    @classmethod
    def from_dto(cls, dto: AgentOutputDTO) -> "AgentResponse":
        return cls(
            agent_id=dto.agent_id,
            name=dto.name,
            system_prompt=dto.system_prompt,
            status=dto.status,
            voice_id=dto.voice_id,
            model_id=dto.model_id,
            stability=dto.stability,
            similarity_boost=dto.similarity_boost,
            created_at=dto.created_at.isoformat(),
            updated_at=dto.updated_at.isoformat(),
        )


class AgentListResponse(BaseModel):
    agents: list[AgentResponse]
    total: int
    limit: int
    offset: int


# ── Endpoints ─────────────────────────────────────────────────────────────────


@router.post("", response_model=AgentResponse, status_code=201)
async def create_agent(
    body: CreateAgentRequest,
    use_case: CreateAgentUseCase = Depends(get_create_agent_use_case),
) -> AgentResponse:
    """Create a new AI agent."""
    dto = CreateAgentInputDTO(
        name=body.name,
        system_prompt=body.system_prompt,
        voice_id=body.voice_id,
        model_id=body.model_id,
        stability=body.stability,
        similarity_boost=body.similarity_boost,
    )
    result = await use_case.execute(dto)
    return AgentResponse.from_dto(result)


@router.get("", response_model=AgentListResponse)
async def list_agents(
    status: str | None = Query(default=None, description="Filter by agent status"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    use_case: ListAgentsUseCase = Depends(get_list_agents_use_case),
) -> AgentListResponse:
    """List all agents, optionally filtered by status."""
    dto = ListAgentsInputDTO(status_filter=status, limit=limit, offset=offset)
    result: AgentListOutputDTO = await use_case.execute(dto)
    return AgentListResponse(
        agents=[AgentResponse.from_dto(a) for a in result.agents],
        total=result.total,
        limit=result.limit,
        offset=result.offset,
    )


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(
    agent_id: str,
    use_case: GetAgentUseCase = Depends(get_get_agent_use_case),
) -> AgentResponse:
    """Retrieve a single agent by ID."""
    result = await use_case.execute(GetAgentInputDTO(agent_id=agent_id))
    return AgentResponse.from_dto(result)
