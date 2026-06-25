"""
Unit tests for domain value objects.
"""
import pytest

from src.domain.exceptions import InvalidPhoneNumberError
from src.domain.value_objects.agent_status import AgentStatus
from src.domain.value_objects.message_role import MessageRole
from src.domain.value_objects.phone_number import PhoneNumber
from src.domain.value_objects.voice_settings import VoiceSettings


class TestPhoneNumber:
    def test_valid_e164(self) -> None:
        pn = PhoneNumber("+15551234567")
        assert str(pn) == "+15551234567"

    def test_strips_whitespace(self) -> None:
        pn = PhoneNumber("  +15551234567  ")
        assert str(pn) == "+15551234567"

    def test_invalid_raises(self) -> None:
        with pytest.raises(InvalidPhoneNumberError):
            PhoneNumber("not-a-phone")

    def test_no_plus_raises(self) -> None:
        with pytest.raises(InvalidPhoneNumberError):
            PhoneNumber("15551234567")

    def test_equality(self) -> None:
        assert PhoneNumber("+15551234567") == PhoneNumber("+15551234567")

    def test_inequality(self) -> None:
        assert PhoneNumber("+15551234567") != PhoneNumber("+442071234567")

    def test_hashable(self) -> None:
        s = {PhoneNumber("+15551234567"), PhoneNumber("+15551234567")}
        assert len(s) == 1


class TestVoiceSettings:
    def test_valid_defaults(self) -> None:
        vs = VoiceSettings(voice_id="abc123")
        assert vs.stability == 0.5
        assert vs.similarity_boost == 0.75

    def test_invalid_stability_raises(self) -> None:
        with pytest.raises(ValueError):
            VoiceSettings(voice_id="abc", stability=1.5)

    def test_immutable(self) -> None:
        vs = VoiceSettings(voice_id="abc")
        with pytest.raises(Exception):  # frozen dataclass
            vs.stability = 0.1  # type: ignore[misc]

    def test_with_stability_returns_new_instance(self) -> None:
        vs1 = VoiceSettings(voice_id="abc")
        vs2 = vs1.with_stability(0.8)
        assert vs2.stability == 0.8
        assert vs1.stability == 0.5  # original unchanged


class TestAgentStatus:
    def test_active_is_available(self) -> None:
        assert AgentStatus.ACTIVE.is_available()

    def test_idle_is_not_available(self) -> None:
        assert not AgentStatus.IDLE.is_available()

    def test_idle_can_activate(self) -> None:
        assert AgentStatus.IDLE.can_activate()

    def test_busy_cannot_activate(self) -> None:
        assert not AgentStatus.BUSY.can_activate()


class TestMessageRole:
    def test_user_is_human(self) -> None:
        assert MessageRole.USER.is_human()

    def test_agent_is_ai(self) -> None:
        assert MessageRole.AGENT.is_ai()

    def test_system_is_neither(self) -> None:
        assert not MessageRole.SYSTEM.is_human()
        assert not MessageRole.SYSTEM.is_ai()
