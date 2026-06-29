"""
ListFeedsUseCase

Returns a paginated list of feeds with optional status filtering.
"""
from __future__ import annotations

from src.application.dtos.feed_dtos import FeedListOutputDTO, ListFeedsInputDTO
from src.application.mappers.feed_mapper import FeedMapper
from src.domain.repositories.feed_repository import IFeedRepository
from src.domain.value_objects.feed_status import FeedStatus


class ListFeedsUseCase:
    def __init__(self, feed_repository: IFeedRepository) -> None:
        self._repo = feed_repository

    async def execute(self, dto: ListFeedsInputDTO) -> FeedListOutputDTO:
        if dto.status_filter:
            feeds = await self._repo.list_by_status(
                FeedStatus(dto.status_filter),
                limit=dto.limit,
                offset=dto.offset,
            )
        else:
            feeds = await self._repo.list_all(limit=dto.limit, offset=dto.offset)

        return FeedListOutputDTO(
            feeds=[FeedMapper.to_output_dto(f) for f in feeds],
            total=len(feeds),
            limit=dto.limit,
            offset=dto.offset,
        )
