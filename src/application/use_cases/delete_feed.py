"""
DeleteFeedUseCase

Hard-deletes a Feed by ID. To merely stop ingestion without removing the
record, use :class:`SetFeedEnabledUseCase` instead.
"""
from __future__ import annotations

from src.application.dtos.feed_dtos import DeleteFeedInputDTO
from src.domain.exceptions import FeedNotFoundError
from src.domain.repositories.feed_repository import IFeedRepository


class DeleteFeedUseCase:
    def __init__(self, feed_repository: IFeedRepository) -> None:
        self._repo = feed_repository

    async def execute(self, dto: DeleteFeedInputDTO) -> None:
        if not await self._repo.exists(dto.feed_id):
            raise FeedNotFoundError(f"Feed '{dto.feed_id}' not found")
        await self._repo.delete(dto.feed_id)
