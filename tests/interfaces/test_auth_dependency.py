"""
Integration tests for the ``get_current_user`` auth dependency.

Verifies that protected routes reject unauthenticated / invalid requests
with 401, that public routes stay open, and that a valid token makes the
authenticated user's ID and roles available to the route handler.

The token validator is overridden with a fake so the tests don't depend on
a real Supabase secret; the validator itself is exercised separately in
``tests/infrastructure/test_supabase_jwt_validator.py``.
"""
from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient

from src.application.dtos.session_dtos import SessionOutputDTO
from src.application.ports.token_validator import ITokenValidator
from src.domain.exceptions import ExpiredTokenError, InvalidTokenError
from src.domain.value_objects.authenticated_user import AuthenticatedUser
from src.interfaces.api.container import (
    get_start_session_use_case,
    get_token_validator,
)
from src.interfaces.api.main import create_app

_VALID_TOKEN = "valid-token"  # noqa: S105 — test fixture, not a real secret


class _FakeValidator(ITokenValidator):
    """Accepts a single known token; rejects everything else."""

    def validate(self, token: str) -> AuthenticatedUser:
        if token == _VALID_TOKEN:
            return AuthenticatedUser(
                user_id="user-from-token", roles=("authenticated", "admin")
            )
        if token == "expired":
            raise ExpiredTokenError("Access token has expired")
        raise InvalidTokenError("Invalid access token")


class _FakeStartSessionUseCase:
    """Returns a canned session echoing the user_id it was handed."""

    async def execute(self, dto) -> SessionOutputDTO:  # type: ignore[no-untyped-def]
        return SessionOutputDTO(
            session_id="sess-1",
            agent_id=dto.agent_id,
            user_id=dto.user_id,
            status="active",
            metadata={},
            started_at=datetime.now(UTC),
            ended_at=None,
            created_at=datetime.now(UTC),
            duration_seconds=None,
        )


@pytest.fixture()
def client() -> TestClient:
    app = create_app()
    app.dependency_overrides[get_token_validator] = lambda: _FakeValidator()
    app.dependency_overrides[get_start_session_use_case] = (
        lambda: _FakeStartSessionUseCase()
    )
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# ── AC 4: protected endpoints require the dependency ──────────────────────────


def test_protected_route_without_token_returns_401(client: TestClient) -> None:
    resp = client.get("/agents")
    assert resp.status_code == 401


def test_protected_route_with_invalid_token_returns_401(client: TestClient) -> None:
    resp = client.get("/agents", headers={"Authorization": "Bearer garbage"})
    assert resp.status_code == 401


# ── AC 2: invalid / expired tokens return 401 ─────────────────────────────────


def test_expired_token_returns_401(client: TestClient) -> None:
    resp = client.post(
        "/sessions",
        headers={"Authorization": "Bearer expired"},
        json={"agent_id": "agent-1"},
    )
    assert resp.status_code == 401
    assert "expired" in resp.json()["detail"].lower()


def test_401_includes_www_authenticate_header(client: TestClient) -> None:
    resp = client.get("/agents")
    assert resp.headers.get("WWW-Authenticate") == "Bearer"


# ── AC 3: user id / roles available to the handler ────────────────────────────


def test_valid_token_injects_user_id_into_handler(client: TestClient) -> None:
    resp = client.post(
        "/sessions",
        headers={"Authorization": f"Bearer {_VALID_TOKEN}"},
        json={"agent_id": "agent-1"},
    )
    assert resp.status_code == 201
    # The handler derived user_id from the token, not the request body.
    assert resp.json()["user_id"] == "user-from-token"


# ── Public endpoints remain open ──────────────────────────────────────────────


def test_health_is_public(client: TestClient) -> None:
    resp = client.get("/health")
    assert resp.status_code in (200, 503)  # depends on DB availability


def test_twilio_webhook_is_public(client: TestClient) -> None:
    # The status webhook requires no auth (Twilio cannot send a bearer token).
    resp = client.post(
        "/calls/webhook/status",
        data={"CallSid": "CA123", "CallStatus": "completed"},
    )
    assert resp.status_code == 204
