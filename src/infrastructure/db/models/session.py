"""ORM model for the ``sessions`` table."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.infrastructure.db.models.base import Base


class SessionModel(Base):
    __tablename__ = "sessions"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, server_default=func.uuid_generate_v4()
    )
    agent_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("agents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="pending", index=True
    )
    metadata_: Mapped[dict] = mapped_column(  # type: ignore[type-arg]
        "metadata", JSONB, nullable=False, server_default="{}"
    )
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
        "AgentModel", back_populates="sessions"
    )
    messages: Mapped[list["MessageModel"]] = relationship(  # type: ignore[name-defined]
        "MessageModel", back_populates="session", cascade="all, delete-orphan"
    )
    calls: Mapped[list["CallModel"]] = relationship(  # type: ignore[name-defined]
        "CallModel", back_populates="session"
    )

    __table_args__ = (
        CheckConstraint(
            "status IN ('pending','active','paused','completed','failed')",
            name="ck_sessions_status",
        ),
    )
