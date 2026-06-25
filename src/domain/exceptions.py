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


# ── Call ───────────────────────────────────────────────────────────────────


class CallNotFoundError(DomainException):
    pass


class InvalidPhoneNumberError(DomainException):
    pass


class CallAlreadyInProgressError(DomainException):
    pass
