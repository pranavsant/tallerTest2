"""ORM model for the ``incidents`` table.

An Incident represents a detected anomaly or event that requires
human or AI-assisted investigation and resolution.
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.infrastructure.db.models.base import Base


class IncidentModel(Base):
    __tablename__ = "incidents"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, server_default=func.uuid_generate_v4()
    )
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    severity: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="medium"
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="open"
    )
    feed_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("feeds.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    assignee_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    # Free-form metadata (tags, source refs, raw payload excerpt, etc.)
    metadata_: Mapped[dict] = mapped_column(  # type: ignore[type-arg]
        "metadata", JSONB, nullable=False, server_default="{}"
    )
    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # ── Relationships ──────────────────────────────────────────────────────
    feed: Mapped["FeedModel | None"] = relationship(  # type: ignore[name-defined]
        "FeedModel", back_populates="incidents"
    )
    assignee: Mapped["UserModel | None"] = relationship(  # type: ignore[name-defined]
        "UserModel",
        back_populates="incidents",
        foreign_keys="IncidentModel.assignee_id",
    )
    alerts: Mapped[list["AlertModel"]] = relationship(  # type: ignore[name-defined]
        "AlertModel", back_populates="incident"
    )

    __table_args__ = (
        CheckConstraint(
            "severity IN ('critical','high','medium','low','info')",
            name="ck_incidents_severity",
        ),
        CheckConstraint(
            "status IN ('open','investigating','resolved','closed','false_positive')",
            name="ck_incidents_status",
        ),
        Index("idx_incidents_severity", "severity"),
        Index("idx_incidents_status", "status"),
        Index("idx_incidents_created_at", "created_at"),
    )
