"""
Unit tests for the Agent entity.

These tests run at pure Python speed — no DB, no HTTP, no mocks needed.
"""
import pytest

from src.domain.entities.agent import Agent
from src.domain.exceptions import InvalidAgentNameError
from src.domain.value_objects.agent_status import AgentStatus
from src.domain.value_objects.voice_settings import VoiceSettings


def _make_agent(**kwargs: object) -> Agent:
    defaults = dict(
        name="Test Agent",
        system_prompt="You are a helpful assistant.",
        voice_settings=VoiceSettings(voice_id="test-voice-id"),
    )
    defaults.update(kwargs)
    return Agent(**defaults)  # type: ignore[arg-type]


class TestAgentCreation:
    def test_creates_with_valid_data(self) -> None:
        agent = _make_agent()
        assert agent.name == "Test Agent"
        assert agent.status == AgentStatus.IDLE

    def test_assigns_uuid_if_no_id_given(self) -> None:
        agent = _make_agent()
        assert len(agent.id) == 36  # UUID4 format

    def test_raises_on_empty_name(self) -> None:
        with pytest.raises(InvalidAgentNameError):
            _make_agent(name="")

    def test_raises_on_name_too_long(self) -> None:
        with pytest.raises(InvalidAgentNameError):
            _make_agent(name="x" * 101)

    def test_raises_on_empty_system_prompt(self) -> None:
        with pytest.raises(ValueError):
            _make_agent(system_prompt="")


class TestAgentStatusTransitions:
    def test_idle_agent_can_activate(self) -> None:
        agent = _make_agent()
        agent.activate()
        assert agent.status == AgentStatus.ACTIVE

    def test_active_agent_can_go_busy(self) -> None:
        agent = _make_agent()
        agent.activate()
        agent.mark_busy()
        assert agent.status == AgentStatus.BUSY

    def test_busy_agent_cannot_activate_directly(self) -> None:
        agent = _make_agent()
        agent.activate()
        agent.mark_busy()
        with pytest.raises(ValueError):
            agent.activate()

    def test_active_agent_can_be_suspended(self) -> None:
        agent = _make_agent()
        agent.activate()
        agent.suspend()
        assert agent.status == AgentStatus.SUSPENDED

    def test_suspended_agent_is_not_available(self) -> None:
        agent = _make_agent()
        agent.activate()
        agent.suspend()
        assert not agent.is_available()

    def test_active_agent_is_available(self) -> None:
        agent = _make_agent()
        agent.activate()
        assert agent.is_available()


class TestAgentEquality:
    def test_same_id_equal(self) -> None:
        agent1 = _make_agent()
        agent2 = Agent(
            agent_id=agent1.id,
            name="Different Name",
            system_prompt="Different prompt",
            voice_settings=VoiceSettings(voice_id="other"),
        )
        assert agent1 == agent2

    def test_different_ids_not_equal(self) -> None:
        assert _make_agent() != _make_agent()
