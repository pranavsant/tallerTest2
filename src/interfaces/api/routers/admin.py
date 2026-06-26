"""
Admin router — /admin

User and role administration. Every endpoint requires the ``admin`` role,
enforced router-wide via ``require_role(Role.ADMIN)`` in main.py, so role
management is itself only manageable by admins (acceptance criterion 4).

Thin controller: validate input → call use case → serialize output.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field

from src.application.dtos.user_dtos import (
    AssignRoleInputDTO,
    ListUsersInputDTO,
    ListUsersOutputDTO,
    SetUserActiveInputDTO,
    UserOutputDTO,
)
from src.application.use_cases.assign_role import AssignRoleUseCase
from src.application.use_cases.list_users import ListUsersUseCase
from src.application.use_cases.set_user_active import SetUserActiveUseCase
from src.domain.value_objects.role import Role
from src.interfaces.api.container import (
    get_assign_role_use_case,
    get_list_users_use_case,
    get_set_user_active_use_case,
)

router = APIRouter()


# ── Schemas ───────────────────────────────────────────────────────────────────


class UserResponse(BaseModel):
    user_id: str
    email: str | None
    role: str | None
    is_active: bool
    created_at: str | None
    last_sign_in_at: str | None

    @classmethod
    def from_dto(cls, dto: UserOutputDTO) -> "UserResponse":
        return cls(
            user_id=dto.user_id,
            email=dto.email,
            role=dto.role,
            is_active=dto.is_active,
            created_at=dto.created_at.isoformat() if dto.created_at else None,
            last_sign_in_at=(
                dto.last_sign_in_at.isoformat() if dto.last_sign_in_at else None
            ),
        )


class UserListResponse(BaseModel):
    users: list[UserResponse]
    page: int
    per_page: int


class AssignRoleRequest(BaseModel):
    # Constrained to the recognised roles so an invalid value is rejected at
    # the edge (422) before reaching the use case.
    role: Role = Field(..., description="Role to assign to the user.")


class SetUserActiveRequest(BaseModel):
    is_active: bool = Field(
        ..., description="True to reactivate the account, False to deactivate it."
    )


# ── Endpoints ─────────────────────────────────────────────────────────────────


@router.get("/users", response_model=UserListResponse)
async def list_users(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=50, ge=1, le=200),
    use_case: ListUsersUseCase = Depends(get_list_users_use_case),
) -> UserListResponse:
    """List users and their assigned roles. Admin only."""
    result: ListUsersOutputDTO = await use_case.execute(
        ListUsersInputDTO(page=page, per_page=per_page)
    )
    return UserListResponse(
        users=[UserResponse.from_dto(u) for u in result.users],
        page=result.page,
        per_page=result.per_page,
    )


@router.put("/users/{user_id}/role", response_model=UserResponse)
async def assign_role(
    user_id: str,
    body: AssignRoleRequest,
    use_case: AssignRoleUseCase = Depends(get_assign_role_use_case),
) -> UserResponse:
    """Assign a role to a user. Admin only."""
    result = await use_case.execute(
        AssignRoleInputDTO(user_id=user_id, role=body.role.value)
    )
    return UserResponse.from_dto(result)


@router.put("/users/{user_id}/status", response_model=UserResponse)
async def set_user_active(
    user_id: str,
    body: SetUserActiveRequest,
    use_case: SetUserActiveUseCase = Depends(get_set_user_active_use_case),
) -> UserResponse:
    """Deactivate or reactivate a user's account. Admin only."""
    result = await use_case.execute(
        SetUserActiveInputDTO(user_id=user_id, is_active=body.is_active)
    )
    return UserResponse.from_dto(result)
