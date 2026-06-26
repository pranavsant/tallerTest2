"""
Domain exceptions — all business-rule violations raised as typed exceptions.
No external imports; these are pure Python.
"""


class DomainException(Exception):
    """Base class for all domain exceptions."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


# ── Agent ──────────────────────────────────────────────────────────────────


class AgentNotFoundError(DomainException):
    pass


class AgentAlreadyExistsError(DomainException):
    pass


class InvalidAgentNameError(DomainException):
    pass


# ── Session ────────────────────────────────────────────────────────────────


class SessionNotFoundError(DomainException):
    pass


class SessionAlreadyActiveError(DomainException):
    pass


class SessionNotActiveError(DomainException):
    pass


# ── Message ────────────────────────────────────────────────────────────────


class EmptyMessageContentError(DomainException):
    pass


class MessageTooLongError(DomainException):
    pass


# ── Auth ───────────────────────────────────────────────────────────────────


class AuthenticationError(DomainException):
    """Base class for authentication failures (maps to HTTP 401)."""


class MissingTokenError(AuthenticationError):
    """No bearer token was supplied on a protected request."""


class InvalidTokenError(AuthenticationError):
    """The token signature is invalid or the token is malformed."""


class ExpiredTokenError(AuthenticationError):
    """The token is well-formed but has expired."""


# ── Call ───────────────────────────────────────────────────────────────────


class CallNotFoundError(DomainException):
    pass


class InvalidPhoneNumberError(DomainException):
    pass


class CallAlreadyInProgressError(DomainException):
    pass
