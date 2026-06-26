"""
Unit tests for SupabaseJWTValidator.

Tokens are minted locally with the same secret/algorithm Supabase uses
(HS256) so the validator can be exercised without a live Supabase project.
"""
from datetime import UTC, datetime, timedelta

import pytest
from jose import jwt

from src.domain.exceptions import ExpiredTokenError, InvalidTokenError
from src.infrastructure.services.supabase_jwt_validator import SupabaseJWTValidator

_SECRET = "test-super-secret-jwt-key"
_AUDIENCE = "authenticated"


def _make_token(secret: str = _SECRET, **overrides) -> str:
    now = datetime.now(UTC)
    claims = {
        "sub": "user-uuid-123",
        "aud": _AUDIENCE,
        "role": "authenticated",
        "exp": now + timedelta(hours=1),
        "iat": now,
        "app_metadata": {"roles": ["admin"]},
    }
    claims.update(overrides)
    return jwt.encode(claims, secret, algorithm="HS256")


class TestSupabaseJWTValidator:
    def test_requires_secret(self) -> None:
        with pytest.raises(ValueError):
            SupabaseJWTValidator(jwt_secret="")

    def test_valid_token_extracts_user_id(self) -> None:
        validator = SupabaseJWTValidator(jwt_secret=_SECRET)
        user = validator.validate(_make_token())
        assert user.user_id == "user-uuid-123"

    def test_valid_token_extracts_roles(self) -> None:
        validator = SupabaseJWTValidator(jwt_secret=_SECRET)
        user = validator.validate(_make_token())
        # Both the top-level postgres role and app_metadata roles are surfaced.
        assert user.has_role("authenticated")
        assert user.has_role("admin")

    def test_wrong_signature_raises_invalid(self) -> None:
        validator = SupabaseJWTValidator(jwt_secret=_SECRET)
        forged = _make_token(secret="a-different-secret")
        with pytest.raises(InvalidTokenError):
            validator.validate(forged)

    def test_expired_token_raises_expired(self) -> None:
        validator = SupabaseJWTValidator(jwt_secret=_SECRET)
        past = datetime.now(UTC) - timedelta(hours=1)
        token = _make_token(exp=past, iat=past - timedelta(hours=2))
        with pytest.raises(ExpiredTokenError):
            validator.validate(token)

    def test_malformed_token_raises_invalid(self) -> None:
        validator = SupabaseJWTValidator(jwt_secret=_SECRET)
        with pytest.raises(InvalidTokenError):
            validator.validate("not.a.jwt")

    def test_wrong_audience_raises_invalid(self) -> None:
        validator = SupabaseJWTValidator(jwt_secret=_SECRET)
        token = _make_token(aud="some-other-audience")
        with pytest.raises(InvalidTokenError):
            validator.validate(token)

    def test_missing_sub_raises_invalid(self) -> None:
        validator = SupabaseJWTValidator(jwt_secret=_SECRET)
        now = datetime.now(UTC)
        # Build claims without a 'sub'.
        token = jwt.encode(
            {"aud": _AUDIENCE, "exp": now + timedelta(hours=1)},
            _SECRET,
            algorithm="HS256",
        )
        with pytest.raises(InvalidTokenError):
            validator.validate(token)
