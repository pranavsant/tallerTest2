"""
Integration tests for the ``require_role`` authorization dependency.

Verifies that role-gated endpoints return:
  - 401 when the request is unauthenticated,
  - 403 when the user is authenticated but lacks the required role,
  - 200/201 when the user holds the required role.

Covers both per-endpoint gating (``/calls`` → admin) and router-wide gating
(``/admin/*`` → admin). The token validator and the admin use cases are
overridden with fakes so the tests touch neither a real Supabase secret nor
the Supabase Admin API.
"""
from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient

from src.application.dtos.call_dtos import CallOutputDTO
from src.application.dtos.user_dtos import (
    ListUsersOutputDTO,
    UserOutputDTO,
)
from src.application.ports.token_validator import ITokenValidator
from src.domain.exceptions import InvalidTokenError
from src.domain.value_objects.authenticated_user import AuthenticatedUser
from src.interfaces.api.container import (
    get_assign_role_use_case,
    get_initiate_call_use_case,
    get_list_users_use_case,
    get_set_user_active_use_case,
    get_token_validator,
)
from src.interfaces.api.main import create_app

# Bearer tokens recognised by the fake validator → (user_id, roles).
_ADMIN_TOKEN = "admin-token"  # noqa: S105 — test fixture
_VIEWER_TOKEN = "viewer-token"  # noqa: S105 — test fixture


class _FakeValidator(ITokenValidator):
    def validate(self, token: str) -> AuthenticatedUser:
        if token == _ADMIN_TOKEN:
            return AuthenticatedUser(user_id="admin-1", roles=("authenticated", "admin"))
        if token == _VIEWER_TOKEN:
            return AuthenticatedUser(user_id="viewer-1", roles=("authenticated", "viewer"))
        raise InvalidTokenError("Invalid access token")


class _FakeInitiateCallUseCase:
    async def execute(self, dto) -> CallOutputDTO:  # type: ignore[no-untyped-def]
        return CallOutputDTO(
            call_id="call-1",
            agent_id=dto.agent_id,
            session_id=dto.session_id,
            to_number=dto.to_phone_number,
            from_number="+15550000000",
            twilio_call_sid="CA1",
            status="queued",
            recording_url=None,
            started_at=None,
            ended_at=None,
            created_at=datetime.now(UTC),
            duration_seconds=None,
        )


class _FakeListUsersUseCase:
    async def execute(self, dto) -> ListUsersOutputDTO:  # type: ignore[no-untyped-def]
        return ListUsersOutputDTO(
            users=[
                UserOutputDTO(
                    user_id="u1",
                    email="a@b.com",
                    role="viewer",
                    is_active=True,
                    created_at=None,
                    last_sign_in_at=None,
                )
            ],
            page=dto.page,
            per_page=dto.per_page,
        )


class _FakeAssignRoleUseCase:
    async def execute(self, dto) -> UserOutputDTO:  # type: ignore[no-untyped-def]
        return UserOutputDTO(
            user_id=dto.user_id,
            email="a@b.com",
            role=dto.role,
            is_active=True,
            created_at=None,
            last_sign_in_at=None,
        )


class _FakeSetUserActiveUseCase:
    async def execute(self, dto) -> UserOutputDTO:  # type: ignore[no-untyped-def]
        return UserOutputDTO(
            user_id=dto.user_id,
            email="a@b.com",
            role="viewer",
            is_active=dto.is_active,
            created_at=None,
            last_sign_in_at=None,
        )


@pytest.fixture()
def client() -> TestClient:
    app = create_app()
    app.dependency_overrides[get_token_validator] = lambda: _FakeValidator()
    app.dependency_overrides[get_initiate_call_use_case] = (
        lambda: _FakeInitiateCallUseCase()
    )
    app.dependency_overrides[get_list_users_use_case] = lambda: _FakeListUsersUseCase()
    app.dependency_overrides[get_assign_role_use_case] = (
        lambda: _FakeAssignRoleUseCase()
    )
    app.dependency_overrides[get_set_user_active_use_case] = (
        lambda: _FakeSetUserActiveUseCase()
    )
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


_CALL_BODY = {"agent_id": "agent-1", "to_phone_number": "+15551234567"}


# ── Per-endpoint gating: POST /calls requires admin ───────────────────────────


def test_calls_without_token_returns_401(client: TestClient) -> None:
    resp = client.post("/calls", json=_CALL_BODY)
    assert resp.status_code == 401


def test_calls_as_viewer_returns_403(client: TestClient) -> None:
    resp = client.post("/calls", json=_CALL_BODY, headers=_auth(_VIEWER_TOKEN))
    assert resp.status_code == 403
    assert "admin" in resp.json()["detail"].lower()


def test_calls_as_admin_succeeds(client: TestClient) -> None:
    resp = client.post("/calls", json=_CALL_BODY, headers=_auth(_ADMIN_TOKEN))
    assert resp.status_code == 201
    assert resp.json()["call_id"] == "call-1"


# ── Router-wide gating: /admin/* requires admin ───────────────────────────────


def test_admin_users_without_token_returns_401(client: TestClient) -> None:
    resp = client.get("/admin/users")
    assert resp.status_code == 401


def test_admin_users_as_viewer_returns_403(client: TestClient) -> None:
    resp = client.get("/admin/users", headers=_auth(_VIEWER_TOKEN))
    assert resp.status_code == 403


def test_admin_users_as_admin_succeeds(client: TestClient) -> None:
    resp = client.get("/admin/users", headers=_auth(_ADMIN_TOKEN))
    assert resp.status_code == 200
    body = resp.json()
    assert body["users"][0]["user_id"] == "u1"


def test_assign_role_as_admin_succeeds(client: TestClient) -> None:
    resp = client.put(
        "/admin/users/u1/role", json={"role": "operator"}, headers=_auth(_ADMIN_TOKEN)
    )
    assert resp.status_code == 200
    assert resp.json()["role"] == "operator"


def test_assign_role_as_viewer_returns_403(client: TestClient) -> None:
    resp = client.put(
        "/admin/users/u1/role", json={"role": "operator"}, headers=_auth(_VIEWER_TOKEN)
    )
    assert resp.status_code == 403


def test_assign_invalid_role_returns_422(client: TestClient) -> None:
    # The Role enum on the request schema rejects unknown values at validation.
    resp = client.put(
        "/admin/users/u1/role", json={"role": "superuser"}, headers=_auth(_ADMIN_TOKEN)
    )
    assert resp.status_code == 422


def test_set_status_as_admin_succeeds(client: TestClient) -> None:
    resp = client.put(
        "/admin/users/u1/status",
        json={"is_active": False},
        headers=_auth(_ADMIN_TOKEN),
    )
    assert resp.status_code == 200
    assert resp.json()["is_active"] is False


def test_set_status_as_viewer_returns_403(client: TestClient) -> None:
    resp = client.put(
        "/admin/users/u1/status",
        json={"is_active": False},
        headers=_auth(_VIEWER_TOKEN),
    )
    assert resp.status_code == 403
