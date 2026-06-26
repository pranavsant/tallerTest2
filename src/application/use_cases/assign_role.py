"""
AssignRoleUseCase — assign an application role to a user.

The role string is validated against the domain :class:`Role` set before any
side effect, so an unknown role never reaches the directory. The directory
adapter persists the role so it rides on the user's next access token.
"""
from __future__ import annotations

from src.application.dtos.user_dtos import AssignRoleInputDTO, UserOutputDTO
from src.application.ports.user_directory import IUserDirectory
from src.domain.exceptions import InvalidRoleError
from src.domain.value_objects.role import Role


class AssignRoleUseCase:
    def __init__(self, user_directory: IUserDirectory) -> None:
        self._directory = user_directory

    async def execute(self, dto: AssignRoleInputDTO) -> UserOutputDTO:
        if not Role.is_valid(dto.role):
            raise InvalidRoleError(
                f"'{dto.role}' is not a valid role. "
                f"Expected one of: {', '.join(Role.values())}."
            )

        user = await self._directory.set_role(dto.user_id, dto.role)
        return UserOutputDTO(
            user_id=user.user_id,
            email=user.email,
            role=user.role,
            created_at=user.created_at,
            last_sign_in_at=user.last_sign_in_at,
        )
