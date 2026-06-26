"""
ITokenValidator — application port for access-token validation.

Implemented in infrastructure by SupabaseJWTValidator. The application
and interfaces layers depend only on this abstraction, never on the
concrete JWT library or Supabase configuration.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from src.domain.value_objects.authenticated_user import AuthenticatedUser


class ITokenValidator(ABC):
    """Abstraction over a bearer-token validator."""

    @abstractmethod
    def validate(self, token: str) -> AuthenticatedUser:
        """
        Validate an access token and extract the authenticated identity.

        Args:
            token: The raw bearer token (without the ``Bearer`` prefix).

        Returns:
            The :class:`AuthenticatedUser` described by the token's claims.

        Raises:
            InvalidTokenError: The signature is invalid or the token is
                malformed / missing required claims.
            ExpiredTokenError: The token is well-formed but has expired.
        """
        ...
