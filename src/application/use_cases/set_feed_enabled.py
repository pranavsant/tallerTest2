"""
SetFeedEnabledUseCase

Toggles a Feed's enabled state. Enabling resumes ingestion; disabling pauses it
while preserving the record (acceptance criterion 3 — never deletes the feed).
"""
from __future__ import annotations

from src.application.dtos.feed_dtos import FeedOutputDTO, SetFeedEnabledInputDTO
from src.application.mappers.feed_mapper import FeedMapper
from src.domain.exceptions import FeedNotFoundError
from src.domain.repositories.feed_repository import IFeedRepository


class SetFeedEnabledUseCase:
    def __init__(self, feed_repository: IFeedRepository) -> None:
        self._repo = feed_repository

    async def execute(self, dto: SetFeedEnabledInputDTO) -> FeedOutputDTO:
        feed = await self._repo.get_by_id(dto.feed_id)
        if feed is None:
            raise FeedNotFoundError(f"Feed '{dto.feed_id}' not found")

        if dto.is_enabled:
            feed.enable()
        else:
            feed.disable()

        await self._repo.save(feed)
        return FeedMapper.to_output_dto(feed)
