"""ORM model for the ``agents`` table."""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, CheckConstraint, DateTime, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.infrastructure.db.models.base import Base


class AgentModel(Base):
    __tablename__ = "agents"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, server_default=func.uuid_generate_v4()
    )
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    system_prompt: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        server_default="idle",
    )
    voice_id: Mapped[str] = mapped_column(Text, nullable=False)
    model_id: Mapped[str] = mapped_column(
        Text, nullable=False, server_default="eleven_turbo_v2"
    )
    stability: Mapped[Decimal] = mapped_column(
        Numeric(4, 3), nullable=False, server_default="0.500"
    )
    similarity_boost: Mapped[Decimal] = mapped_column(
        Numeric(4, 3), nullable=False, server_default="0.750"
    )
    style: Mapped[Decimal] = mapped_column(
        Numeric(4, 3), nullable=False, server_default="0.000"
    )
    use_speaker_boost: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="true"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # ── Relationships ──────────────────────────────────────────────────────
    sessions: Mapped[list["SessionModel"]] = relationship(  # type: ignore[name-defined]
        "SessionModel", back_populates="agent", cascade="all, delete-orphan"
    )
    calls: Mapped[list["CallModel"]] = relationship(  # type: ignore[name-defined]
        "CallModel", back_populates="agent", cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint("char_length(name) BETWEEN 1 AND 100", name="ck_agents_name_length"),
        CheckConstraint(
            "status IN ('idle','active','busy','offline','suspended')",
            name="ck_agents_status",
        ),
        CheckConstraint("stability BETWEEN 0 AND 1", name="ck_agents_stability"),
        CheckConstraint(
            "similarity_boost BETWEEN 0 AND 1", name="ck_agents_similarity_boost"
        ),
        CheckConstraint("style BETWEEN 0 AND 1", name="ck_agents_style"),
    )
