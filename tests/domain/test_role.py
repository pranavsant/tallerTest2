"""Unit tests for the Role value object."""
from src.domain.value_objects.role import Role


class TestRole:
    def test_values_are_the_three_roles(self) -> None:
        assert set(Role.values()) == {"admin", "operator", "viewer"}

    def test_compares_equal_to_its_string(self) -> None:
        assert Role.ADMIN == "admin"
        assert Role.OPERATOR.value == "operator"

    def test_is_valid_accepts_known_roles(self) -> None:
        assert Role.is_valid("admin")
        assert Role.is_valid("operator")
        assert Role.is_valid("viewer")

    def test_is_valid_rejects_unknown_role(self) -> None:
        assert not Role.is_valid("superuser")
        assert not Role.is_valid("")
