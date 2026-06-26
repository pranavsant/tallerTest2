"""
SetUserActiveUseCase — deactivate or reactivate a user's account.

Deactivating blocks the user from signing in; reactivating restores access.
Authorization (admin-only) is enforced at the interface layer. The directory
adapter performs the side effect against the identity provider.
"""
from __future__ import annotations

from src.application.dtos.user_dtos import SetUserActiveInputDTO, UserOutputDTO
from src.application.ports.user_directory import IUserDirectory


class SetUserActiveUseCase:
    def __init__(self, user_directory: IUserDirectory) -> None:
        self._directory = user_directory

    async def execute(self, dto: SetUserActiveInputDTO) -> UserOutputDTO:
        user = await self._directory.set_active(dto.user_id, dto.is_active)
        return UserOutputDTO(
            user_id=user.user_id,
            email=user.email,
            role=user.role,
            is_active=user.is_active,
            created_at=user.created_at,
            last_sign_in_at=user.last_sign_in_at,
        )
