"""
FeedMapper — converts Feed entities to/from DTOs.
No I/O; pure data transformation.
"""
from __future__ import annotations

from src.application.dtos.feed_dtos import FeedOutputDTO
from src.domain.entities.feed import Feed


class FeedMapper:
    @staticmethod
    def to_output_dto(feed: Feed) -> FeedOutputDTO:
        return FeedOutputDTO(
            feed_id=feed.id,
            name=feed.name,
            source_type=feed.source_type.value,
            status=feed.status.value,
            endpoint_url=feed.endpoint_url,
            polling_interval_seconds=feed.polling_interval_seconds,
            config=feed.config,
            is_enabled=feed.is_enabled,
            last_ingested_at=feed.last_ingested_at,
            created_at=feed.created_at,
            updated_at=feed.updated_at,
        )
