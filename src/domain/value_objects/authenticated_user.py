"""
AuthenticatedUser value object.

Immutable representation of the identity extracted from a validated
access token. Carries the user's ID and the roles granted to them.

This is a pure domain concept: it knows nothing about JWTs, HTTP, or
how the token was validated — only about *who* the authenticated
principal is.
"""
from __future__ import annotations


class AuthenticatedUser:
    """
    The identity of an authenticated principal.

    >>> user = AuthenticatedUser(user_id="abc-123", roles=("authenticated", "admin"))
    >>> user.user_id
    'abc-123'
    >>> user.has_role("admin")
    True
    >>> user.has_role("editor")
    False
    """

    def __init__(self, user_id: str, roles: tuple[str, ...] = ()) -> None:
        if not user_id:
            raise ValueError("AuthenticatedUser requires a non-empty user_id")
        self._user_id = user_id
        # Normalise to an ordered, de-duplicated tuple so the value object is
        # both immutable and hashable while ignoring incidental ordering.
        self._roles: tuple[str, ...] = tuple(dict.fromkeys(roles))

    @property
    def user_id(self) -> str:
        return self._user_id

    @property
    def roles(self) -> tuple[str, ...]:
        return self._roles

    def has_role(self, role: str) -> bool:
        return role in self._roles

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, AuthenticatedUser):
            return NotImplemented
        return self._user_id == other._user_id and set(self._roles) == set(
            other._roles
        )

    def __hash__(self) -> int:
        return hash((self._user_id, frozenset(self._roles)))

    def __repr__(self) -> str:
        return f"AuthenticatedUser(user_id='{self._user_id}', roles={self._roles!r})"
