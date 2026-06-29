"""
Unit tests for the feed use cases.

Uses an in-memory repository stub — no Supabase, no network.
"""
from __future__ import annotations

import pytest

from src.application.dtos.feed_dtos import (
    CreateFeedInputDTO,
    DeleteFeedInputDTO,
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
from src.domain.entities.feed import Feed
from src.domain.exceptions import (
    FeedNotFoundError,
    InvalidFeedSourceTypeError,
    InvalidFeedUrlError,
)
from src.domain.repositories.feed_repository import IFeedRepository
from src.domain.value_objects.feed_status import FeedStatus


class InMemoryFeedRepository(IFeedRepository):
    def __init__(self) -> None:
        self._store: dict[str, Feed] = {}

    async def save(self, feed: Feed) -> None:
        self._store[feed.id] = feed

    async def get_by_id(self, feed_id: str) -> Feed | None:
        return self._store.get(feed_id)

    async def list_by_status(
        self, status: FeedStatus, *, limit: int = 50, offset: int = 0
    ) -> list[Feed]:
        return [f for f in self._store.values() if f.status == status]

    async def list_all(self, *, limit: int = 50, offset: int = 0) -> list[Feed]:
        return list(self._store.values())

    async def delete(self, feed_id: str) -> None:
        self._store.pop(feed_id, None)

    async def exists(self, feed_id: str) -> bool:
        return feed_id in self._store


@pytest.fixture()
def repo() -> InMemoryFeedRepository:
    return InMemoryFeedRepository()


async def _make_feed(repo: InMemoryFeedRepository) -> str:
    result = await CreateFeedUseCase(repo).execute(
        CreateFeedInputDTO(
            name="Webhook feed",
            source_type="webhook",
            endpoint_url="https://example.com/hook",
            polling_interval_seconds=30,
        )
    )
    return result.feed_id


class TestCreateFeed:
    async def test_creates_and_persists(self, repo: InMemoryFeedRepository) -> None:
        result = await CreateFeedUseCase(repo).execute(
            CreateFeedInputDTO(name="F1", source_type="manual")
        )
        assert result.source_type == "manual"
        assert result.status == "active"
        assert result.is_enabled is True
        assert await repo.exists(result.feed_id)

    async def test_rejects_unknown_source_type(
        self, repo: InMemoryFeedRepository
    ) -> None:
        with pytest.raises(InvalidFeedSourceTypeError):
            await CreateFeedUseCase(repo).execute(
                CreateFeedInputDTO(name="Bad", source_type="carrier-pigeon")
            )

    async def test_rejects_missing_url_for_polling(
        self, repo: InMemoryFeedRepository
    ) -> None:
        with pytest.raises(InvalidFeedUrlError):
            await CreateFeedUseCase(repo).execute(
                CreateFeedInputDTO(name="Poll", source_type="polling")
            )


class TestGetAndList:
    async def test_get_missing_raises(self, repo: InMemoryFeedRepository) -> None:
        with pytest.raises(FeedNotFoundError):
            await GetFeedUseCase(repo).execute(GetFeedInputDTO(feed_id="nope"))

    async def test_list_all(self, repo: InMemoryFeedRepository) -> None:
        await _make_feed(repo)
        result = await ListFeedsUseCase(repo).execute(ListFeedsInputDTO())
        assert result.total == 1
        assert result.feeds[0].polling_interval_seconds == 30

    async def test_list_filtered_by_status(
        self, repo: InMemoryFeedRepository
    ) -> None:
        feed_id = await _make_feed(repo)
        await SetFeedEnabledUseCase(repo).execute(
            SetFeedEnabledInputDTO(feed_id=feed_id, is_enabled=False)
        )
        active = await ListFeedsUseCase(repo).execute(
            ListFeedsInputDTO(status_filter="active")
        )
        disabled = await ListFeedsUseCase(repo).execute(
            ListFeedsInputDTO(status_filter="disabled")
        )
        assert active.total == 0
        assert disabled.total == 1


class TestUpdate:
    async def test_partial_update_changes_only_supplied_fields(
        self, repo: InMemoryFeedRepository
    ) -> None:
        feed_id = await _make_feed(repo)
        result = await UpdateFeedUseCase(repo).execute(
            UpdateFeedInputDTO(feed_id=feed_id, name="Renamed")
        )
        assert result.name == "Renamed"
        assert result.endpoint_url == "https://example.com/hook"
        assert result.polling_interval_seconds == 30

    async def test_can_clear_polling_interval(
        self, repo: InMemoryFeedRepository
    ) -> None:
        feed_id = await _make_feed(repo)
        result = await UpdateFeedUseCase(repo).execute(
            UpdateFeedInputDTO(feed_id=feed_id, polling_interval_seconds=None)
        )
        assert result.polling_interval_seconds is None

    async def test_update_missing_raises(self, repo: InMemoryFeedRepository) -> None:
        with pytest.raises(FeedNotFoundError):
            await UpdateFeedUseCase(repo).execute(
                UpdateFeedInputDTO(feed_id="nope", name="X")
            )


class TestEnableDisableAndDelete:
    async def test_toggle_does_not_delete(
        self, repo: InMemoryFeedRepository
    ) -> None:
        feed_id = await _make_feed(repo)
        await SetFeedEnabledUseCase(repo).execute(
            SetFeedEnabledInputDTO(feed_id=feed_id, is_enabled=False)
        )
        assert await repo.exists(feed_id)

    async def test_delete_removes_feed(self, repo: InMemoryFeedRepository) -> None:
        feed_id = await _make_feed(repo)
        await DeleteFeedUseCase(repo).execute(DeleteFeedInputDTO(feed_id=feed_id))
        assert not await repo.exists(feed_id)

    async def test_delete_missing_raises(self, repo: InMemoryFeedRepository) -> None:
        with pytest.raises(FeedNotFoundError):
            await DeleteFeedUseCase(repo).execute(DeleteFeedInputDTO(feed_id="nope"))
