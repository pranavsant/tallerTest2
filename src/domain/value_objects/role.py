"""
Role value object.

The fixed set of application roles Overseer AI recognises. Authentication
identity (the *who*) lives in :class:`AuthenticatedUser`; this enumerates the
*what they may do* dimension.

Pure domain: no knowledge of JWTs, Supabase, or HTTP. The ordering below is
also the privilege ordering — ``ADMIN`` is the most privileged.
"""
from __future__ import annotations

from enum import Enum


class Role(str, Enum):
    """The application roles recognised across the system.

    Inherits from ``str`` so the members compare and serialise as their plain
    string value (``Role.ADMIN == "admin"``), which keeps the value object
    interchangeable with the role strings carried on a JWT or stored in the
    database.
    """

    ADMIN = "admin"
    OPERATOR = "operator"
    VIEWER = "viewer"

    @classmethod
    def values(cls) -> tuple[str, ...]:
        """All role values, in privilege order (most privileged first)."""
        return tuple(r.value for r in cls)

    @classmethod
    def is_valid(cls, value: str) -> bool:
        return value in cls.values()
