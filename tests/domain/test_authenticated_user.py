"""
Unit tests for the AuthenticatedUser value object.
"""
import pytest

from src.domain.value_objects.authenticated_user import AuthenticatedUser


class TestAuthenticatedUser:
    def test_carries_user_id_and_roles(self) -> None:
        user = AuthenticatedUser(user_id="abc-123", roles=("authenticated", "admin"))
        assert user.user_id == "abc-123"
        assert user.roles == ("authenticated", "admin")

    def test_empty_user_id_raises(self) -> None:
        with pytest.raises(ValueError):
            AuthenticatedUser(user_id="")

    def test_has_role(self) -> None:
        user = AuthenticatedUser(user_id="u", roles=("admin",))
        assert user.has_role("admin")
        assert not user.has_role("editor")

    def test_roles_default_empty(self) -> None:
        user = AuthenticatedUser(user_id="u")
        assert user.roles == ()

    def test_roles_deduplicated(self) -> None:
        user = AuthenticatedUser(user_id="u", roles=("admin", "admin", "authenticated"))
        assert user.roles == ("admin", "authenticated")

    def test_equality_ignores_role_order(self) -> None:
        a = AuthenticatedUser(user_id="u", roles=("admin", "authenticated"))
        b = AuthenticatedUser(user_id="u", roles=("authenticated", "admin"))
        assert a == b

    def test_inequality_on_user_id(self) -> None:
        assert AuthenticatedUser(user_id="a") != AuthenticatedUser(user_id="b")

    def test_hashable(self) -> None:
        s = {
            AuthenticatedUser(user_id="u", roles=("admin",)),
            AuthenticatedUser(user_id="u", roles=("admin",)),
        }
        assert len(s) == 1
