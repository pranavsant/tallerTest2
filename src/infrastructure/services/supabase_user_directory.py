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

    # ── Mapping ────────────────────────────────────────────────────────────

    @staticmethod
    def _to_directory_user(user: Any) -> DirectoryUser:
        app_metadata: dict[str, Any] = getattr(user, "app_metadata", None) or {}
        return DirectoryUser(
            user_id=user.id,
            email=getattr(user, "email", None),
            role=_extract_role(app_metadata),
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


def _looks_like_not_found(exc: Exception) -> bool:
    text = str(exc).lower()
    return "not found" in text or "user_not_found" in text
