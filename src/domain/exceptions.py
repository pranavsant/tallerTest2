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


# ── Authorization ────────────────────────────────────────────────────────────


class AuthorizationError(DomainException):
    """The principal is authenticated but lacks permission (maps to HTTP 403)."""


class InsufficientRoleError(AuthorizationError):
    """The authenticated user does not hold a role required for the action."""


# ── User / Role administration ───────────────────────────────────────────────


class UserNotFoundError(DomainException):
    """No user exists with the given identifier."""


class InvalidRoleError(DomainException):
    """The supplied role is not one of the recognised application roles."""


# ── Feed ───────────────────────────────────────────────────────────────────


class FeedNotFoundError(DomainException):
    """No feed exists with the given identifier."""


class InvalidFeedNameError(DomainException):
    """The feed name is empty or exceeds the maximum length."""


class InvalidFeedSourceTypeError(DomainException):
    """The supplied source type is not one of the recognised feed types."""


class InvalidFeedUrlError(DomainException):
    """The endpoint URL is malformed or missing when the source type requires it."""


class InvalidPollingIntervalError(DomainException):
    """The polling interval is outside the permitted bounds."""


# ── Raw feed items ───────────────────────────────────────────────────────────


class MissingFeedReferenceError(DomainException):
    """A raw feed item was constructed without the owning feed's identifier."""


class InvalidContentHashError(DomainException):
    """A raw feed item was constructed without a usable content hash."""


class EmptyFeedItemError(DomainException):
    """A raw feed item carries neither a title nor any content."""


# ── Call ───────────────────────────────────────────────────────────────────


class CallNotFoundError(DomainException):
    pass


class InvalidPhoneNumberError(DomainException):
    pass


class CallAlreadyInProgressError(DomainException):
    pass
