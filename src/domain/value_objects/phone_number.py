"""
PhoneNumber value object.

Immutable, self-validating E.164 phone number.
"""
from __future__ import annotations

import re

from src.domain.exceptions import InvalidPhoneNumberError

_E164_PATTERN = re.compile(r"^\+[1-9]\d{7,14}$")


class PhoneNumber:
    """
    E.164 phone number value object.

    >>> PhoneNumber("+15551234567")
    PhoneNumber('+15551234567')
    >>> PhoneNumber("not-a-number")
    Traceback (most recent call last):
        ...
    InvalidPhoneNumberError: ...
    """

    def __init__(self, value: str) -> None:
        stripped = value.strip()
        if not _E164_PATTERN.match(stripped):
            raise InvalidPhoneNumberError(
                f"'{value}' is not a valid E.164 phone number (e.g. +15551234567)"
            )
        self._value = stripped

    @property
    def value(self) -> str:
        return self._value

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, PhoneNumber):
            return NotImplemented
        return self._value == other._value

    def __hash__(self) -> int:
        return hash(self._value)

    def __repr__(self) -> str:
        return f"PhoneNumber('{self._value}')"

    def __str__(self) -> str:
        return self._value
