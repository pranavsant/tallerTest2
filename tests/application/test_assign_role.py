"""Unit tests for the role-administration use cases."""
import pytest

from src.application.dtos.user_dtos import AssignRoleInputDTO, ListUsersInputDTO
from src.application.ports.user_directory import DirectoryUser, IUserDirectory
from src.application.use_cases.assign_role import AssignRoleUseCase
from src.application.use_cases.list_users import ListUsersUseCase
from src.domain.exceptions import InvalidRoleError, UserNotFoundError


class _FakeDirectory(IUserDirectory):
    """In-memory directory keyed by user id."""

    def __init__(self, users: dict[str, DirectoryUser]) -> None:
        self._users = users
        self.set_calls: list[tuple[str, str]] = []

    async def list_users(self, page: int = 1, per_page: int = 50) -> list[DirectoryUser]:
        return list(self._users.values())

    async def set_role(self, user_id: str, role: str) -> DirectoryUser:
        self.set_calls.append((user_id, role))
        existing = self._users.get(user_id)
        if existing is None:
            raise UserNotFoundError(f"User '{user_id}' not found")
        updated = DirectoryUser(
            user_id=existing.user_id, email=existing.email, role=role
        )
        self._users[user_id] = updated
        return updated


@pytest.fixture()
def directory() -> _FakeDirectory:
    return _FakeDirectory(
        {"u1": DirectoryUser(user_id="u1", email="a@b.com", role="viewer")}
    )


class TestAssignRoleUseCase:
    async def test_assigns_valid_role(self, directory: _FakeDirectory) -> None:
        use_case = AssignRoleUseCase(directory)
        result = await use_case.execute(AssignRoleInputDTO(user_id="u1", role="admin"))
        assert result.role == "admin"
        assert directory.set_calls == [("u1", "admin")]

    async def test_rejects_invalid_role_before_any_side_effect(
        self, directory: _FakeDirectory
    ) -> None:
        use_case = AssignRoleUseCase(directory)
        with pytest.raises(InvalidRoleError):
            await use_case.execute(AssignRoleInputDTO(user_id="u1", role="superuser"))
        # The directory was never touched.
        assert directory.set_calls == []

    async def test_unknown_user_propagates_not_found(
        self, directory: _FakeDirectory
    ) -> None:
        use_case = AssignRoleUseCase(directory)
        with pytest.raises(UserNotFoundError):
            await use_case.execute(AssignRoleInputDTO(user_id="ghost", role="operator"))


class TestListUsersUseCase:
    async def test_returns_users_with_roles(self, directory: _FakeDirectory) -> None:
        use_case = ListUsersUseCase(directory)
        result = await use_case.execute(ListUsersInputDTO(page=1, per_page=10))
        assert len(result.users) == 1
        assert result.users[0].user_id == "u1"
        assert result.users[0].role == "viewer"
