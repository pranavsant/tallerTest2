"""
GetFeedUseCase

Retrieves a single Feed by ID.
"""
from __future__ import annotations

from src.application.dtos.feed_dtos import FeedOutputDTO, GetFeedInputDTO
from src.application.mappers.feed_mapper import FeedMapper
from src.domain.exceptions import FeedNotFoundError
from src.domain.repositories.feed_repository import IFeedRepository


class GetFeedUseCase:
    def __init__(self, feed_repository: IFeedRepository) -> None:
        self._repo = feed_repository

    async def execute(self, dto: GetFeedInputDTO) -> FeedOutputDTO:
        feed = await self._repo.get_by_id(dto.feed_id)
        if feed is None:
            raise FeedNotFoundError(f"Feed '{dto.feed_id}' not found")
        return FeedMapper.to_output_dto(feed)
