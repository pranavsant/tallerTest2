"""
MessageRole value object.

Represents who authored a message within a session conversation.
"""
from __future__ import annotations

from enum import Enum


class MessageRole(str, Enum):
    USER = "user"
    AGENT = "agent"
    SYSTEM = "system"

    def is_human(self) -> bool:
        return self == MessageRole.USER

    def is_ai(self) -> bool:
        return self == MessageRole.AGENT
