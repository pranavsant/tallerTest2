"""
Unit tests for the Session entity.
"""
import pytest

from src.domain.entities.session import Session
from src.domain.exceptions import SessionAlreadyActiveError, SessionNotActiveError
from src.domain.value_objects.session_status import SessionStatus


def _make_session(**kwargs: object) -> Session:
    defaults = dict(agent_id="agent-123", user_id="user-456")
    defaults.update(kwargs)
    return Session(**defaults)  # type: ignore[arg-type]


class TestSessionLifecycle:
    def test_new_session_is_pending(self) -> None:
        s = _make_session()
        assert s.status == SessionStatus.PENDING

    def test_start_transitions_to_active(self) -> None:
        s = _make_session()
        s.start()
        assert s.status == SessionStatus.ACTIVE
        assert s.started_at is not None

    def test_start_twice_raises(self) -> None:
        s = _make_session()
        s.start()
        with pytest.raises(SessionAlreadyActiveError):
            s.start()

    def test_complete_sets_ended_at(self) -> None:
        s = _make_session()
        s.start()
        s.complete()
        assert s.status == SessionStatus.COMPLETED
        assert s.ended_at is not None

    def test_fail_records_reason(self) -> None:
        s = _make_session()
        s.start()
        s.fail("network error")
        assert s.status == SessionStatus.FAILED
        assert s.metadata.get("failure_reason") == "network error"

    def test_assert_active_raises_when_not_active(self) -> None:
        s = _make_session()
        with pytest.raises(SessionNotActiveError):
            s.assert_active()

    def test_duration_seconds_increases_over_time(self) -> None:
        s = _make_session()
        s.start()
        duration = s.duration_seconds()
        assert duration is not None and duration >= 0

    def test_complete_is_idempotent(self) -> None:
        s = _make_session()
        s.start()
        s.complete()
        s.complete()  # should not raise
        assert s.status == SessionStatus.COMPLETED
