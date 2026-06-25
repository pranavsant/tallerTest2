"""
Unit tests for the SessionOrchestrator domain service.
"""
import pytest

from src.domain.entities.agent import Agent
from src.domain.entities.session import Session
from src.domain.exceptions import SessionNotActiveError
from src.domain.services.session_orchestrator import SessionOrchestrator
from src.domain.value_objects.agent_status import AgentStatus
from src.domain.value_objects.session_status import SessionStatus
from src.domain.value_objects.voice_settings import VoiceSettings


def _agent(status: AgentStatus = AgentStatus.IDLE) -> Agent:
    a = Agent(
        name="Test",
        system_prompt="You are helpful.",
        voice_settings=VoiceSettings(voice_id="v1"),
    )
    if status == AgentStatus.ACTIVE:
        a.activate()
    return a


def _session(agent_id: str = "a1") -> Session:
    return Session(agent_id=agent_id, user_id="u1")


class TestSessionOrchestrator:
    def setup_method(self) -> None:
        self.orchestrator = SessionOrchestrator()

    def test_begin_session_requires_active_agent(self) -> None:
        agent = _agent(AgentStatus.IDLE)
        session = _session(agent.id)
        with pytest.raises(ValueError, match="not available"):
            self.orchestrator.begin_session(agent, session)

    def test_begin_session_marks_agent_busy(self) -> None:
        agent = _agent(AgentStatus.ACTIVE)
        session = _session(agent.id)
        self.orchestrator.begin_session(agent, session)
        assert agent.status == AgentStatus.BUSY
        assert session.status == SessionStatus.ACTIVE

    def test_end_session_completes_session(self) -> None:
        agent = _agent(AgentStatus.ACTIVE)
        session = _session(agent.id)
        self.orchestrator.begin_session(agent, session)
        self.orchestrator.end_session(agent, session)
        assert session.status == SessionStatus.COMPLETED

    def test_build_user_message_requires_active_session(self) -> None:
        session = _session()
        with pytest.raises(SessionNotActiveError):
            self.orchestrator.build_user_message(session, "hello")

    def test_build_user_message_succeeds_on_active_session(self) -> None:
        agent = _agent(AgentStatus.ACTIVE)
        session = _session(agent.id)
        self.orchestrator.begin_session(agent, session)
        msg = self.orchestrator.build_user_message(session, "hello")
        assert msg.content == "hello"

    def test_build_agent_message_with_audio(self) -> None:
        agent = _agent(AgentStatus.ACTIVE)
        session = _session(agent.id)
        self.orchestrator.begin_session(agent, session)
        msg = self.orchestrator.build_agent_message(
            session, "hi there", audio_url="https://example.com/audio.mp3"
        )
        assert msg.audio_url == "https://example.com/audio.mp3"
