"""
Integration tests for the /feeds router.

Verifies:
  - reads (GET) are open to any authenticated role,
  - writes (POST/PUT/DELETE) require the admin role (401 / 403 / success),
  - edge validation rejects bad source types and out-of-range intervals (422).

The use cases are replaced with an in-memory-backed fake so the tests touch
neither Supabase nor the network. The token validator is faked too.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from src.application.ports.token_validator import ITokenValidator
from src.application.use_cases.create_feed import CreateFeedUseCase
from src.application.use_cases.delete_feed import DeleteFeedUseCase
from src.application.use_cases.get_feed import GetFeedUseCase
from src.application.use_cases.list_feeds import ListFeedsUseCase
from src.application.use_cases.set_feed_enabled import SetFeedEnabledUseCase
from src.application.use_cases.update_feed import UpdateFeedUseCase
from src.domain.entities.feed import Feed
from src.domain.exceptions import InvalidTokenError
from src.domain.repositories.feed_repository import IFeedRepository
from src.domain.value_objects.authenticated_user import AuthenticatedUser
from src.domain.value_objects.feed_status import FeedStatus
from src.interfaces.api.container import (
    get_create_feed_use_case,
    get_delete_feed_use_case,
    get_get_feed_use_case,
    get_list_feeds_use_case,
    get_set_feed_enabled_use_case,
    get_token_validator,
    get_update_feed_use_case,
)
from src.interfaces.api.main import create_app

_ADMIN_TOKEN = "admin-token"  # noqa: S105 — test fixture
_VIEWER_TOKEN = "viewer-token"  # noqa: S105 — test fixture


class _FakeValidator(ITokenValidator):
    def validate(self, token: str) -> AuthenticatedUser:
        if token == _ADMIN_TOKEN:
            return AuthenticatedUser(user_id="admin-1", roles=("authenticated", "admin"))
        if token == _VIEWER_TOKEN:
            return AuthenticatedUser(
                user_id="viewer-1", roles=("authenticated", "viewer")
            )
        raise InvalidTokenError("Invalid access token")


class _InMemoryFeedRepository(IFeedRepository):
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
def repo() -> _InMemoryFeedRepository:
    return _InMemoryFeedRepository()


@pytest.fixture()
def client(repo: _InMemoryFeedRepository) -> TestClient:
    app = create_app()
    app.dependency_overrides[get_token_validator] = lambda: _FakeValidator()
    app.dependency_overrides[get_create_feed_use_case] = lambda: CreateFeedUseCase(repo)
    app.dependency_overrides[get_get_feed_use_case] = lambda: GetFeedUseCase(repo)
    app.dependency_overrides[get_list_feeds_use_case] = lambda: ListFeedsUseCase(repo)
    app.dependency_overrides[get_update_feed_use_case] = lambda: UpdateFeedUseCase(repo)
    app.dependency_overrides[get_delete_feed_use_case] = lambda: DeleteFeedUseCase(repo)
    app.dependency_overrides[get_set_feed_enabled_use_case] = (
        lambda: SetFeedEnabledUseCase(repo)
    )
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


_CREATE_BODY = {
    "name": "Sensor feed",
    "source_type": "webhook",
    "endpoint_url": "https://example.com/hook",
    "polling_interval_seconds": 60,
}


def _create_as_admin(client: TestClient) -> str:
    resp = client.post("/feeds", json=_CREATE_BODY, headers=_auth(_ADMIN_TOKEN))
    assert resp.status_code == 201, resp.text
    return resp.json()["feed_id"]


# ── Authentication ─────────────────────────────────────────────────────────────


def test_list_without_token_returns_401(client: TestClient) -> None:
    assert client.get("/feeds").status_code == 401


# ── Reads: open to any authenticated role ──────────────────────────────────────


def test_viewer_can_list(client: TestClient) -> None:
    _create_as_admin(client)
    resp = client.get("/feeds", headers=_auth(_VIEWER_TOKEN))
    assert resp.status_code == 200
    assert resp.json()["total"] == 1


def test_viewer_can_get(client: TestClient) -> None:
    feed_id = _create_as_admin(client)
    resp = client.get(f"/feeds/{feed_id}", headers=_auth(_VIEWER_TOKEN))
    assert resp.status_code == 200
    assert resp.json()["feed_id"] == feed_id


def test_get_missing_returns_404(client: TestClient) -> None:
    resp = client.get("/feeds/does-not-exist", headers=_auth(_VIEWER_TOKEN))
    assert resp.status_code == 404


# ── Writes: admin only ──────────────────────────────────────────────────────────


def test_viewer_cannot_create(client: TestClient) -> None:
    resp = client.post("/feeds", json=_CREATE_BODY, headers=_auth(_VIEWER_TOKEN))
    assert resp.status_code == 403


def test_admin_can_create(client: TestClient) -> None:
    resp = client.post("/feeds", json=_CREATE_BODY, headers=_auth(_ADMIN_TOKEN))
    assert resp.status_code == 201
    body = resp.json()
    assert body["source_type"] == "webhook"
    assert body["polling_interval_seconds"] == 60


def test_viewer_cannot_update(client: TestClient) -> None:
    feed_id = _create_as_admin(client)
    resp = client.put(
        f"/feeds/{feed_id}", json={"name": "X"}, headers=_auth(_VIEWER_TOKEN)
    )
    assert resp.status_code == 403


def test_admin_can_update(client: TestClient) -> None:
    feed_id = _create_as_admin(client)
    resp = client.put(
        f"/feeds/{feed_id}", json={"name": "Renamed"}, headers=_auth(_ADMIN_TOKEN)
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "Renamed"


def test_viewer_cannot_toggle(client: TestClient) -> None:
    feed_id = _create_as_admin(client)
    resp = client.put(
        f"/feeds/{feed_id}/enabled",
        json={"is_enabled": False},
        headers=_auth(_VIEWER_TOKEN),
    )
    assert resp.status_code == 403


def test_admin_toggle_disables_without_deleting(client: TestClient) -> None:
    feed_id = _create_as_admin(client)
    resp = client.put(
        f"/feeds/{feed_id}/enabled",
        json={"is_enabled": False},
        headers=_auth(_ADMIN_TOKEN),
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["is_enabled"] is False
    assert body["status"] == "disabled"
    # Still retrievable — not deleted.
    assert client.get(f"/feeds/{feed_id}", headers=_auth(_VIEWER_TOKEN)).status_code == 200


def test_viewer_cannot_delete(client: TestClient) -> None:
    feed_id = _create_as_admin(client)
    resp = client.delete(f"/feeds/{feed_id}", headers=_auth(_VIEWER_TOKEN))
    assert resp.status_code == 403


def test_admin_can_delete(client: TestClient) -> None:
    feed_id = _create_as_admin(client)
    resp = client.delete(f"/feeds/{feed_id}", headers=_auth(_ADMIN_TOKEN))
    assert resp.status_code == 204
    assert client.get(f"/feeds/{feed_id}", headers=_auth(_ADMIN_TOKEN)).status_code == 404


# ── Validation ──────────────────────────────────────────────────────────────────


def test_invalid_source_type_rejected_at_edge(client: TestClient) -> None:
    body = {**_CREATE_BODY, "source_type": "carrier-pigeon"}
    resp = client.post("/feeds", json=body, headers=_auth(_ADMIN_TOKEN))
    assert resp.status_code == 422


def test_out_of_range_interval_rejected_at_edge(client: TestClient) -> None:
    body = {**_CREATE_BODY, "polling_interval_seconds": 1}
    resp = client.post("/feeds", json=body, headers=_auth(_ADMIN_TOKEN))
    assert resp.status_code == 422


def test_missing_url_for_webhook_rejected_by_entity(client: TestClient) -> None:
    # Pydantic passes (url optional) but the entity requires it → 422.
    body = {"name": "No URL", "source_type": "webhook"}
    resp = client.post("/feeds", json=body, headers=_auth(_ADMIN_TOKEN))
    assert resp.status_code == 422


def test_malformed_url_rejected_by_entity(client: TestClient) -> None:
    body = {**_CREATE_BODY, "endpoint_url": "not-a-url"}
    resp = client.post("/feeds", json=body, headers=_auth(_ADMIN_TOKEN))
    assert resp.status_code == 422
