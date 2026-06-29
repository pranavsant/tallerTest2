"""
Feeds router — /feeds

CRUD for feed sources: the inputs to the ingestion engine.

Read operations (GET) are available to any authenticated user; write
operations (POST/PUT/DELETE and the enable/disable toggle) require the
``admin`` role (acceptance criterion 4). The router itself is mounted under a
router-wide authentication dependency in main.py; the admin gate is attached
per write-endpoint here so reads stay open to all roles.

Thin controller: validate input → call use case → serialize output.
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field

from src.application.dtos.feed_dtos import (
    _UNSET,
    CreateFeedInputDTO,
    DeleteFeedInputDTO,
    FeedListOutputDTO,
    FeedOutputDTO,
    GetFeedInputDTO,
    ListFeedsInputDTO,
    SetFeedEnabledInputDTO,
    UpdateFeedInputDTO,
)
from src.application.use_cases.create_feed import CreateFeedUseCase
from src.application.use_cases.delete_feed import DeleteFeedUseCase
from src.application.use_cases.get_feed import GetFeedUseCase
from src.application.use_cases.list_feeds import ListFeedsUseCase
from src.application.use_cases.set_feed_enabled import SetFeedEnabledUseCase
from src.application.use_cases.update_feed import UpdateFeedUseCase
from src.domain.value_objects.feed_source_type import FeedSourceType
from src.domain.value_objects.feed_status import FeedStatus
from src.domain.value_objects.role import Role
from src.interfaces.api.container import (
    get_create_feed_use_case,
    get_delete_feed_use_case,
    get_get_feed_use_case,
    get_list_feeds_use_case,
    get_set_feed_enabled_use_case,
    get_update_feed_use_case,
)
from src.interfaces.api.core.dependencies import require_role

router = APIRouter()

# Polling-interval bounds surfaced to the edge so out-of-range values are
# rejected with a 422 before reaching the use case. Kept in sync with the
# domain entity's bounds (the entity remains the source of truth).
_MIN_INTERVAL = 5
_MAX_INTERVAL = 86_400

# Reusable admin gate for write operations.
_admin_only = [Depends(require_role(Role.ADMIN))]


# ── Request / response schemas ────────────────────────────────────────────────


class CreateFeedRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    source_type: FeedSourceType = Field(..., description="Kind of ingestion source.")
    endpoint_url: str | None = Field(default=None, max_length=2048)
    polling_interval_seconds: int | None = Field(
        default=None, ge=_MIN_INTERVAL, le=_MAX_INTERVAL
    )
    config: dict[str, Any] = Field(default_factory=dict)


class UpdateFeedRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    source_type: FeedSourceType | None = Field(default=None)
    endpoint_url: str | None = Field(default=None, max_length=2048)
    polling_interval_seconds: int | None = Field(
        default=None, ge=_MIN_INTERVAL, le=_MAX_INTERVAL
    )
    config: dict[str, Any] | None = Field(default=None)


class SetFeedEnabledRequest(BaseModel):
    is_enabled: bool = Field(
        ..., description="True to enable the feed, False to disable it."
    )


class FeedResponse(BaseModel):
    feed_id: str
    name: str
    source_type: str
    status: str
    endpoint_url: str | None
    polling_interval_seconds: int | None
    config: dict[str, Any]
    is_enabled: bool
    last_ingested_at: str | None
    created_at: str
    updated_at: str

    @classmethod
    def from_dto(cls, dto: FeedOutputDTO) -> "FeedResponse":
        return cls(
            feed_id=dto.feed_id,
            name=dto.name,
            source_type=dto.source_type,
            status=dto.status,
            endpoint_url=dto.endpoint_url,
            polling_interval_seconds=dto.polling_interval_seconds,
            config=dto.config,
            is_enabled=dto.is_enabled,
            last_ingested_at=(
                dto.last_ingested_at.isoformat() if dto.last_ingested_at else None
            ),
            created_at=dto.created_at.isoformat(),
            updated_at=dto.updated_at.isoformat(),
        )


class FeedListResponse(BaseModel):
    feeds: list[FeedResponse]
    total: int
    limit: int
    offset: int


# ── Read endpoints (any authenticated role) ───────────────────────────────────


@router.get("", response_model=FeedListResponse)
async def list_feeds(
    status: FeedStatus | None = Query(
        default=None, description="Filter by feed status."
    ),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    use_case: ListFeedsUseCase = Depends(get_list_feeds_use_case),
) -> FeedListResponse:
    """List feed sources, optionally filtered by status. Any role."""
    dto = ListFeedsInputDTO(
        status_filter=status.value if status else None,
        limit=limit,
        offset=offset,
    )
    result: FeedListOutputDTO = await use_case.execute(dto)
    return FeedListResponse(
        feeds=[FeedResponse.from_dto(f) for f in result.feeds],
        total=result.total,
        limit=result.limit,
        offset=result.offset,
    )


@router.get("/{feed_id}", response_model=FeedResponse)
async def get_feed(
    feed_id: str,
    use_case: GetFeedUseCase = Depends(get_get_feed_use_case),
) -> FeedResponse:
    """Retrieve a single feed source by ID. Any role."""
    result = await use_case.execute(GetFeedInputDTO(feed_id=feed_id))
    return FeedResponse.from_dto(result)


# ── Write endpoints (admin only) ───────────────────────────────────────────────


@router.post("", response_model=FeedResponse, status_code=201, dependencies=_admin_only)
async def create_feed(
    body: CreateFeedRequest,
    use_case: CreateFeedUseCase = Depends(get_create_feed_use_case),
) -> FeedResponse:
    """Create a new feed source. Admin only."""
    dto = CreateFeedInputDTO(
        name=body.name,
        source_type=body.source_type.value,
        endpoint_url=body.endpoint_url,
        polling_interval_seconds=body.polling_interval_seconds,
        config=body.config,
    )
    result = await use_case.execute(dto)
    return FeedResponse.from_dto(result)


@router.put("/{feed_id}", response_model=FeedResponse, dependencies=_admin_only)
async def update_feed(
    feed_id: str,
    body: UpdateFeedRequest,
    use_case: UpdateFeedUseCase = Depends(get_update_feed_use_case),
) -> FeedResponse:
    """Update a feed source. Admin only.

    Only fields present in the request body are applied; ``endpoint_url`` and
    ``polling_interval_seconds`` may be explicitly set to null to clear them.
    """
    fields_set = body.model_fields_set
    dto = UpdateFeedInputDTO(
        feed_id=feed_id,
        name=body.name,
        source_type=body.source_type.value if body.source_type else None,
        # Distinguish "omitted" from "explicit null" so a clear is honoured
        # while an absent field is left untouched.
        endpoint_url=(
            body.endpoint_url if "endpoint_url" in fields_set else _UNSET
        ),
        polling_interval_seconds=(
            body.polling_interval_seconds
            if "polling_interval_seconds" in fields_set
            else _UNSET
        ),
        config=body.config,
    )
    result = await use_case.execute(dto)
    return FeedResponse.from_dto(result)


@router.put(
    "/{feed_id}/enabled", response_model=FeedResponse, dependencies=_admin_only
)
async def set_feed_enabled(
    feed_id: str,
    body: SetFeedEnabledRequest,
    use_case: SetFeedEnabledUseCase = Depends(get_set_feed_enabled_use_case),
) -> FeedResponse:
    """Enable or disable a feed source without deleting it. Admin only."""
    result = await use_case.execute(
        SetFeedEnabledInputDTO(feed_id=feed_id, is_enabled=body.is_enabled)
    )
    return FeedResponse.from_dto(result)


@router.delete("/{feed_id}", status_code=204, dependencies=_admin_only)
async def delete_feed(
    feed_id: str,
    use_case: DeleteFeedUseCase = Depends(get_delete_feed_use_case),
) -> None:
    """Delete a feed source. Admin only."""
    await use_case.execute(DeleteFeedInputDTO(feed_id=feed_id))
