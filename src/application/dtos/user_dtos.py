"""
DTOs for the user / role administration use cases.

Input and output contracts spoken by the admin use cases. The interfaces layer
maps HTTP request/response schemas to and from these; the use cases never see
HTTP types.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class UserOutputDTO:
    user_id: str
    email: str | None
    role: str | None
    created_at: datetime | None
    last_sign_in_at: datetime | None


@dataclass(frozen=True)
class ListUsersInputDTO:
    page: int = 1
    per_page: int = 50


@dataclass(frozen=True)
class ListUsersOutputDTO:
    users: list[UserOutputDTO]
    page: int
    per_page: int


@dataclass(frozen=True)
class AssignRoleInputDTO:
    user_id: str
    role: str
