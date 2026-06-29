"""
CreateFeedUseCase

Creates a new Feed source and persists it.
"""
from __future__ import annotations

from src.application.dtos.feed_dtos import CreateFeedInputDTO, FeedOutputDTO
from src.application.mappers.feed_mapper import FeedMapper
from src.domain.entities.feed import Feed
from src.domain.exceptions import InvalidFeedSourceTypeError
from src.domain.repositories.feed_repository import IFeedRepository
from src.domain.value_objects.feed_source_type import FeedSourceType


class CreateFeedUseCase:
    """Creates a new Feed."""

    def __init__(self, feed_repository: IFeedRepository) -> None:
        self._repo = feed_repository

    async def execute(self, dto: CreateFeedInputDTO) -> FeedOutputDTO:
        source_type = _parse_source_type(dto.source_type)

        feed = Feed(
            name=dto.name,
            source_type=source_type,
            endpoint_url=dto.endpoint_url,
            polling_interval_seconds=dto.polling_interval_seconds,
            config=dto.config,
        )

        await self._repo.save(feed)
        return FeedMapper.to_output_dto(feed)


def _parse_source_type(value: str) -> FeedSourceType:
    """Translate a raw source-type string into the domain enum.

    Shared validation entry point so create/update reject unknown types with a
    consistent domain exception rather than a bare ``ValueError``.
    """
    if not FeedSourceType.is_valid(value):
        raise InvalidFeedSourceTypeError(
            f"'{value}' is not a valid feed source type. "
            f"Expected one of: {', '.join(FeedSourceType.values())}."
        )
    return FeedSourceType(value)
