"""
Shared FastAPI dependency providers.

Centralises the most common ``Depends(...)`` targets so that routers import
from one stable location rather than directly from infrastructure modules.

Example usage in a router::

    from fastapi import Depends
    from sqlalchemy.ext.asyncio import AsyncSession
    from src.interfaces.api.core.dependencies import get_db_session

    @router.get("/example")
    async def example(db: AsyncSession = Depends(get_db_session)) -> ...:
        ...
"""
from __future__ import annotations

from collections.abc import AsyncGenerator, Callable, Coroutine
from typing import Any

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.ports.token_validator import ITokenValidator
from src.domain.exceptions import AuthenticationError
from src.domain.value_objects.authenticated_user import AuthenticatedUser
from src.domain.value_objects.role import Role
from src.infrastructure.db import get_db
from src.interfaces.api.container import get_token_validator


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Thin re-export of ``src.infrastructure.db.get_db``.

    Routers should import ``get_db_session`` from this module so they stay
    decoupled from the infrastructure layer's internal path.
    """
    async for session in get_db():
        yield session


# ── Authentication ──────────────────────────────────────────────────────────

# ``auto_error=False`` lets us raise a uniform 401 (with a WWW-Authenticate
# header) for both the "no token" and "bad token" cases, rather than the
# 403 FastAPI would otherwise return when the header is absent.
_bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    validator: ITokenValidator = Depends(get_token_validator),
) -> AuthenticatedUser:
    """
    FastAPI dependency that authenticates the request.

    Extracts the bearer token from the ``Authorization`` header, validates
    its signature and expiry via the configured token validator, and returns
    the resulting :class:`AuthenticatedUser` (carrying ``user_id`` and
    ``roles``) for injection into route handlers.

    Raises HTTP 401 when the token is missing, malformed, or expired.
    """
    if credentials is None or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        return validator.validate(credentials.credentials)
    except AuthenticationError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=exc.message,
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


# ── Authorization ─────────────────────────────────────────────────────────────


def require_role(
    role: Role | str,
) -> Callable[[AuthenticatedUser], Coroutine[Any, Any, AuthenticatedUser]]:
    """
    Build a FastAPI dependency that enforces the given role.

    The returned dependency first authenticates the request (reusing
    :func:`get_current_user`, so a missing/invalid token still yields 401),
    then checks that the authenticated user holds ``role``. If not, it raises
    HTTP 403.

    Usage at the endpoint level::

        @router.post("", dependencies=[Depends(require_role(Role.ADMIN))])
        async def configure_feed(...): ...

    Or to also receive the user in the handler::

        async def handler(user: AuthenticatedUser = Depends(require_role(Role.ADMIN))):
            ...

    Attaching it as a router-level dependency protects every endpoint on that
    router without each handler having to opt in.
    """
    required = role.value if isinstance(role, Role) else role

    async def _checker(
        current_user: AuthenticatedUser = Depends(get_current_user),
    ) -> AuthenticatedUser:
        if not current_user.has_role(required):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires the '{required}' role",
            )
        return current_user

    return _checker
