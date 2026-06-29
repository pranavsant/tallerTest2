"""
IFeedFetcher — application port for pulling raw items from a feed source.

Implemented in infrastructure by concrete fetchers (RSS, HTTP/JSON API, …).
Each fetcher knows how to talk to one *kind* of source and translate its
payload into provider-agnostic :class:`FetchedItemDTO` objects. It performs no
normalisation beyond shaping the DTO and no persistence.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from src.application.dtos.ingestion_dtos import FetchedItemDTO
from src.domain.entities.feed import Feed


class IFeedFetcher(ABC):
    """Abstraction over a source-specific feed fetcher."""

    @abstractmethod
    def supports(self, feed: Feed) -> bool:
        """Whether this fetcher can pull items for the given feed."""
        ...

    @abstractmethod
    async def fetch(self, feed: Feed) -> list[FetchedItemDTO]:
        """Pull the current set of items from *feed*'s source.

        Raises an exception on transport/parse failure so the caller can apply
        retry/backoff. Returns an empty list when the source has no items.
        """
        ...
