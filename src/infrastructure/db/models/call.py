"""ORM model for the ``calls`` table (raw Twilio telephony records)."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.infrastructure.db.models.base import Base


class CallModel(Base):
    __tablename__ = "calls"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, server_default=func.uuid_generate_v4()
    )
    agent_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("agents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    session_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("sessions.id", ondelete="SET NULL"),
        nullable=True,
    )
    to_number: Mapped[str] = mapped_column(Text, nullable=False)
    from_number: Mapped[str] = mapped_column(Text, nullable=False)
    twilio_call_sid: Mapped[str | None] = mapped_column(Text, nullable=True, unique=True, index=True)
    status: Mapped[str] = mapped_column(
        Text, nullable=False, server_default="queued", index=True
    )
    recording_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    ended_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # ── Relationships ──────────────────────────────────────────────────────
    agent: Mapped["AgentModel"] = relationship(  # type: ignore[name-defined]
        "AgentModel", back_populates="calls"
    )
    session: Mapped["SessionModel | None"] = relationship(  # type: ignore[name-defined]
        "SessionModel", back_populates="calls"
    )
    call_logs: Mapped[list["CallLogModel"]] = relationship(  # type: ignore[name-defined]
        "CallLogModel", back_populates="call", cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint(
            "status IN ('queued','ringing','in-progress','completed','failed','no-answer','busy','canceled')",
            name="ck_calls_status",
        ),
    )
