"""
UpdateFeedUseCase

Applies a partial update to an existing Feed. Each supplied field is routed
through the entity's validating setters, so URL/source-type/interval invariants
are enforced exactly as they are on creation.
"""
from __future__ import annotations

from src.application.dtos.feed_dtos import (
    _UNSET,
    FeedOutputDTO,
    UpdateFeedInputDTO,
)
from src.application.mappers.feed_mapper import FeedMapper
from src.application.use_cases.create_feed import _parse_source_type
from src.domain.exceptions import FeedNotFoundError
from src.domain.repositories.feed_repository import IFeedRepository


class UpdateFeedUseCase:
    def __init__(self, feed_repository: IFeedRepository) -> None:
        self._repo = feed_repository

    async def execute(self, dto: UpdateFeedInputDTO) -> FeedOutputDTO:
        feed = await self._repo.get_by_id(dto.feed_id)
        if feed is None:
            raise FeedNotFoundError(f"Feed '{dto.feed_id}' not found")

        # source_type first: the endpoint_url invariant depends on it.
        if dto.source_type is not None:
            feed.source_type = _parse_source_type(dto.source_type)

        if dto.name is not None:
            feed.name = dto.name

        if dto.endpoint_url is not _UNSET:
            feed.endpoint_url = dto.endpoint_url

        if dto.polling_interval_seconds is not _UNSET:
            feed.polling_interval_seconds = dto.polling_interval_seconds

        if dto.config is not None:
            feed.config = dto.config

        await self._repo.save(feed)
        return FeedMapper.to_output_dto(feed)
