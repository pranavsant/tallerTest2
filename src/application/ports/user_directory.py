"""
IUserDirectory — application port for reading and administering user identities.

Implemented in infrastructure by an adapter over the Supabase Auth Admin API.
The application layer depends only on this abstraction, never on the Supabase
SDK or how roles happen to be persisted (here: the user's ``app_metadata``).
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class DirectoryUser:
    """A user identity as seen by the directory.

    A plain data holder (not a domain entity): it is the port's transport type,
    carrying just what the role-administration use cases need.

    ``is_active`` is the account's sign-in status: ``False`` means the account
    has been deactivated and the user can no longer authenticate.
    """

    user_id: str
    email: str | None
    role: str | None
    is_active: bool = True
    created_at: datetime | None = None
    last_sign_in_at: datetime | None = None


class IUserDirectory(ABC):
    """Abstraction over the identity provider's user-administration surface."""

    @abstractmethod
    async def list_users(self, page: int = 1, per_page: int = 50) -> list[DirectoryUser]:
        """Return a page of users with their currently-assigned role."""
        ...

    @abstractmethod
    async def set_role(self, user_id: str, role: str) -> DirectoryUser:
        """
        Assign ``role`` to the user, replacing any existing role.

        The role is written so that it is carried on the user's next access
        token. Returns the updated user.

        Raises:
            UserNotFoundError: No user exists with ``user_id``.
        """
        ...

    @abstractmethod
    async def set_active(self, user_id: str, is_active: bool) -> DirectoryUser:
        """
        Activate or deactivate the user's account.

        Deactivating (``is_active=False``) blocks the user from signing in and
        invalidates their ability to obtain new tokens; reactivating restores
        it. Returns the updated user.

        Raises:
            UserNotFoundError: No user exists with ``user_id``.
        """
        ...
