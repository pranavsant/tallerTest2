"""
ListUsersUseCase — page through the directory's users and their roles.

Used by the admin panel to display every user alongside their currently
assigned role. Authorization (admin-only) is enforced at the interface layer.
"""
from __future__ import annotations

from src.application.dtos.user_dtos import (
    ListUsersInputDTO,
    ListUsersOutputDTO,
    UserOutputDTO,
)
from src.application.ports.user_directory import DirectoryUser, IUserDirectory


class ListUsersUseCase:
    def __init__(self, user_directory: IUserDirectory) -> None:
        self._directory = user_directory

    async def execute(self, dto: ListUsersInputDTO) -> ListUsersOutputDTO:
        users = await self._directory.list_users(page=dto.page, per_page=dto.per_page)
        return ListUsersOutputDTO(
            users=[_to_output(u) for u in users],
            page=dto.page,
            per_page=dto.per_page,
        )


def _to_output(user: DirectoryUser) -> UserOutputDTO:
    return UserOutputDTO(
        user_id=user.user_id,
        email=user.email,
        role=user.role,
        is_active=user.is_active,
        created_at=user.created_at,
        last_sign_in_at=user.last_sign_in_at,
    )
