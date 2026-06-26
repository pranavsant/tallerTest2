"""Unit tests for the SetUserActiveUseCase."""
import pytest

from src.application.dtos.user_dtos import SetUserActiveInputDTO
from src.application.ports.user_directory import DirectoryUser, IUserDirectory
from src.application.use_cases.set_user_active import SetUserActiveUseCase
from src.domain.exceptions import UserNotFoundError


class _FakeDirectory(IUserDirectory):
    """In-memory directory keyed by user id."""

    def __init__(self, users: dict[str, DirectoryUser]) -> None:
        self._users = users
        self.active_calls: list[tuple[str, bool]] = []

    async def list_users(self, page: int = 1, per_page: int = 50) -> list[DirectoryUser]:
        return list(self._users.values())

    async def set_role(self, user_id: str, role: str) -> DirectoryUser:  # pragma: no cover
        raise NotImplementedError

    async def set_active(self, user_id: str, is_active: bool) -> DirectoryUser:
        self.active_calls.append((user_id, is_active))
        existing = self._users.get(user_id)
        if existing is None:
            raise UserNotFoundError(f"User '{user_id}' not found")
        updated = DirectoryUser(
            user_id=existing.user_id,
            email=existing.email,
            role=existing.role,
            is_active=is_active,
        )
        self._users[user_id] = updated
        return updated


@pytest.fixture()
def directory() -> _FakeDirectory:
    return _FakeDirectory(
        {"u1": DirectoryUser(user_id="u1", email="a@b.com", role="viewer", is_active=True)}
    )


class TestSetUserActiveUseCase:
    async def test_deactivates_user(self, directory: _FakeDirectory) -> None:
        use_case = SetUserActiveUseCase(directory)
        result = await use_case.execute(
            SetUserActiveInputDTO(user_id="u1", is_active=False)
        )
        assert result.is_active is False
        assert directory.active_calls == [("u1", False)]

    async def test_reactivates_user(self, directory: _FakeDirectory) -> None:
        use_case = SetUserActiveUseCase(directory)
        await use_case.execute(SetUserActiveInputDTO(user_id="u1", is_active=False))
        result = await use_case.execute(
            SetUserActiveInputDTO(user_id="u1", is_active=True)
        )
        assert result.is_active is True
        assert directory.active_calls == [("u1", False), ("u1", True)]

    async def test_unknown_user_propagates_not_found(
        self, directory: _FakeDirectory
    ) -> None:
        use_case = SetUserActiveUseCase(directory)
        with pytest.raises(UserNotFoundError):
            await use_case.execute(
                SetUserActiveInputDTO(user_id="ghost", is_active=False)
            )
