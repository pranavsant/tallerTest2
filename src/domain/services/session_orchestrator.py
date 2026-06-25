"""
SessionOrchestrator — domain service.

Encapsulates multi-entity coordination rules that don't belong to a single
entity. Receives its dependencies via constructor (no I/O).
"""
from __future__ import annotations

from src.domain.entities.agent import Agent
from src.domain.entities.message import Message
from src.domain.entities.session import Session
from src.domain.exceptions import SessionNotActiveError
from src.domain.value_objects.message_role import MessageRole
from src.domain.value_objects.session_status import SessionStatus


class SessionOrchestrator:
    """
    Coordinates the Agent ↔ Session ↔ Message lifecycle.

    Rules enforced here:
    - An agent must be available to start a session.
    - An agent is marked BUSY when a session is started.
    - An agent returns to ACTIVE when its session ends.
    - Messages may only be added to an active session.
    """

    def begin_session(self, agent: Agent, session: Session) -> None:
        """
        Validate and transition both agent and session into an active state.

        Raises:
            ValueError: if the agent is not available.
            SessionAlreadyActiveError: if the session is already active.
        """
        if not agent.is_available():
            raise ValueError(
                f"Agent '{agent.id}' is not available (status={agent.status}). "
                "Only ACTIVE agents can start sessions."
            )
        session.start()
        agent.mark_busy()

    def end_session(self, agent: Agent, session: Session) -> None:
        """
        Complete a session and free the agent.

        Idempotent — safe to call on an already-completed session.
        """
        session.complete()
        # Only release the agent if it was busy with this session
        if agent.status.can_go_offline() or agent.status == agent.status.BUSY:
            try:
                agent.activate()
            except ValueError:
                pass  # Agent may already be in a valid post-session state

    def fail_session(self, agent: Agent, session: Session, reason: str) -> None:
        """Mark session as failed and release the agent."""
        session.fail(reason)
        try:
            agent.activate()
        except ValueError:
            pass

    def build_user_message(self, session: Session, content: str) -> Message:
        """
        Factory: create a user Message scoped to an active Session.

        Raises:
            SessionNotActiveError: if the session cannot receive messages.
        """
        session.assert_active()
        return Message(
            session_id=session.id,
            role=MessageRole.USER,
            content=content,
        )

    def build_agent_message(
        self,
        session: Session,
        content: str,
        audio_url: str | None = None,
    ) -> Message:
        """
        Factory: create an agent response Message.

        Raises:
            SessionNotActiveError: if the session cannot receive messages.
        """
        session.assert_active()
        message = Message(
            session_id=session.id,
            role=MessageRole.AGENT,
            content=content,
        )
        if audio_url:
            message.attach_audio(audio_url)
        return message

    def is_session_resumable(self, session: Session) -> bool:
        return session.status == SessionStatus.PAUSED
