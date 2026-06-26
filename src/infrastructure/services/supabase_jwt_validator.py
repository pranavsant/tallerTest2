"""
SupabaseJWTValidator

Implements ITokenValidator by verifying Supabase-issued JWTs.

Supabase signs access tokens with HS256 using the project's JWT secret.
This adapter verifies the signature and expiry, then maps the token's
claims into a domain :class:`AuthenticatedUser`. All library-specific
errors are re-raised as domain authentication exceptions so the
application and interfaces layers stay JWT-library agnostic.
"""
from __future__ import annotations

from typing import Any

from jose import ExpiredSignatureError, JWTError, jwt

from src.application.ports.token_validator import ITokenValidator
from src.domain.exceptions import ExpiredTokenError, InvalidTokenError
from src.domain.value_objects.authenticated_user import AuthenticatedUser

# Supabase stamps every access token with this audience claim.
_SUPABASE_AUDIENCE = "authenticated"
_ALGORITHM = "HS256"


class SupabaseJWTValidator(ITokenValidator):
    """Validates Supabase JWTs using the shared HS256 secret."""

    def __init__(self, jwt_secret: str, audience: str = _SUPABASE_AUDIENCE) -> None:
        if not jwt_secret:
            # Misconfiguration: refusing every request is safer than
            # accepting unsigned tokens.
            raise ValueError("SupabaseJWTValidator requires a non-empty jwt_secret")
        self._secret = jwt_secret
        self._audience = audience

    def validate(self, token: str) -> AuthenticatedUser:
        try:
            claims: dict[str, Any] = jwt.decode(
                token,
                self._secret,
                algorithms=[_ALGORITHM],
                audience=self._audience,
            )
        except ExpiredSignatureError as exc:
            raise ExpiredTokenError("Access token has expired") from exc
        except JWTError as exc:
            raise InvalidTokenError("Invalid access token") from exc

        user_id = claims.get("sub")
        if not user_id:
            raise InvalidTokenError("Access token is missing the 'sub' claim")

        return AuthenticatedUser(user_id=user_id, roles=_extract_roles(claims))


def _extract_roles(claims: dict[str, Any]) -> tuple[str, ...]:
    """
    Collect roles from the claims Supabase populates.

    * ``role`` — the Postgres role (usually ``authenticated``).
    * ``app_metadata.roles`` / ``app_metadata.role`` — application-level
      roles assigned by the project (admin, etc.).
    """
    roles: list[str] = []

    top_level_role = claims.get("role")
    if isinstance(top_level_role, str) and top_level_role:
        roles.append(top_level_role)

    app_metadata = claims.get("app_metadata")
    if isinstance(app_metadata, dict):
        meta_roles = app_metadata.get("roles")
        if isinstance(meta_roles, list):
            roles.extend(r for r in meta_roles if isinstance(r, str) and r)
        meta_role = app_metadata.get("role")
        if isinstance(meta_role, str) and meta_role:
            roles.append(meta_role)

    return tuple(roles)
