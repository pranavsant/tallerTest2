"""
SupabaseUserDirectory

Implements IUserDirectory over the Supabase Auth Admin API. Roles are stored
in each user's ``app_metadata`` so they are stamped into the user's access
token by Supabase and read back by :class:`SupabaseJWTValidator` — keeping the
JWT the single source of truth for authorization at request time.

Requires the Supabase **service-role** key (the admin API is privileged); the
shared client is created with that key in ``supabase_client.py``.

All SDK-specific failures are re-raised as domain exceptions so the
application and interfaces layers stay provider-agnostic.
"""
from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from supabase import AsyncClient
from supabase_auth.types import AdminUserAttributes

from src.application.ports.user_directory import DirectoryUser, IUserDirectory
from src.domain.exceptions import UserNotFoundError

# The key under app_metadata that holds the user's application roles. The JWT
# validator reads both ``app_metadata.roles`` (list) and ``app_metadata.role``
# (scalar); we write both so either reader resolves the same role.
_ROLES_KEY = "roles"
_ROLE_KEY = "role"

# Supabase deactivates an account by "banning" it for a duration. There is no
# unbounded option, so we use a very long ban to mean "deactivated" and the
# sentinel ``"none"`` to lift it. A banned account cannot sign in or refresh a
# token, which is exactly our "deactivated" semantics.
_BAN_DURATION_DEACTIVATE = "876000h"  # ~100 years
_BAN_DURATION_REACTIVATE = "none"


class SupabaseUserDirectory(IUserDirectory):
    """Supabase Auth Admin–backed implementation of IUserDirectory."""

    def __init__(self, client: AsyncClient) -> None:
        self._client = client

    async def list_users(
        self, page: int = 1, per_page: int = 50
    ) -> list[DirectoryUser]:
        try:
            users = await self._client.auth.admin.list_users(
                page=page, per_page=per_page
            )
        except Exception as exc:  # noqa: BLE001 — normalise SDK error
            raise RuntimeError(f"Failed to list users: {exc}") from exc

        return [self._to_directory_user(u) for u in users]

    async def set_role(self, user_id: str, role: str) -> DirectoryUser:
        try:
            response = await self._client.auth.admin.update_user_by_id(
                user_id,
                AdminUserAttributes(
                    app_metadata={_ROLES_KEY: [role], _ROLE_KEY: role}
                ),
            )
        except Exception as exc:  # noqa: BLE001 — normalise SDK error
            # The admin API raises when the user id is unknown; surface that as
            # a domain not-found rather than a generic 500.
            if _looks_like_not_found(exc):
                raise UserNotFoundError(f"User '{user_id}' not found") from exc
            raise RuntimeError(f"Failed to assign role to '{user_id}': {exc}") from exc

        user = getattr(response, "user", None)
        if user is None:
            raise UserNotFoundError(f"User '{user_id}' not found")
        return self._to_directory_user(user)

    async def set_active(self, user_id: str, is_active: bool) -> DirectoryUser:
        ban_duration = (
            _BAN_DURATION_REACTIVATE if is_active else _BAN_DURATION_DEACTIVATE
        )
        try:
            response = await self._client.auth.admin.update_user_by_id(
                user_id,
                AdminUserAttributes(ban_duration=ban_duration),
            )
        except Exception as exc:  # noqa: BLE001 — normalise SDK error
            if _looks_like_not_found(exc):
                raise UserNotFoundError(f"User '{user_id}' not found") from exc
            verb = "reactivate" if is_active else "deactivate"
            raise RuntimeError(
                f"Failed to {verb} user '{user_id}': {exc}"
            ) from exc

        user = getattr(response, "user", None)
        if user is None:
            raise UserNotFoundError(f"User '{user_id}' not found")
        return self._to_directory_user(user)

    # ── Mapping ────────────────────────────────────────────────────────────

    @staticmethod
    def _to_directory_user(user: Any) -> DirectoryUser:
        app_metadata: dict[str, Any] = getattr(user, "app_metadata", None) or {}
        return DirectoryUser(
            user_id=user.id,
            email=getattr(user, "email", None),
            role=_extract_role(app_metadata),
            is_active=_is_active(getattr(user, "banned_until", None)),
            created_at=getattr(user, "created_at", None),
            last_sign_in_at=getattr(user, "last_sign_in_at", None),
        )


def _extract_role(app_metadata: dict[str, Any]) -> str | None:
    """Read the assigned application role from ``app_metadata``.

    Prefers the first entry of the ``roles`` list, falling back to the scalar
    ``role`` key. Returns ``None`` when no application role has been assigned.
    """
    roles = app_metadata.get(_ROLES_KEY)
    if isinstance(roles, list):
        for r in roles:
            if isinstance(r, str) and r:
                return r
    role = app_metadata.get(_ROLE_KEY)
    if isinstance(role, str) and role:
        return role
    return None


def _is_active(banned_until: Any) -> bool:
    """Derive account status from Supabase's ``banned_until``.

    The account is inactive only while ``banned_until`` is a timestamp in the
    future. A missing value, or one already in the past (an expired ban),
    means the account is active.
    """
    if banned_until is None:
        return True

    if isinstance(banned_until, datetime):
        banned_dt = banned_until
    elif isinstance(banned_until, str):
        # Supabase serialises a trailing "Z"; normalise it for fromisoformat.
        text = banned_until.replace("Z", "+00:00")
        try:
            banned_dt = datetime.fromisoformat(text)
        except ValueError:
            # Unparseable but present → treat conservatively as banned.
            return False
    else:
        return True

    if banned_dt.tzinfo is None:
        banned_dt = banned_dt.replace(tzinfo=UTC)
    return banned_dt <= datetime.now(UTC)


def _looks_like_not_found(exc: Exception) -> bool:
    text = str(exc).lower()
    return "not found" in text or "user_not_found" in text
