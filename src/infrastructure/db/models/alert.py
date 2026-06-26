"""ORM model for the ``alerts`` table.

An Alert is a notification generated from a Feed event or an Incident
that may trigger an automated or human response (e.g. an outbound AI call).
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.infrastructure.db.models.base import Base


class AlertModel(Base):
    __tablename__ = "alerts"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, server_default=func.uuid_generate_v4()
    )
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    severity: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="medium"
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="pending"
    )
    # Optional link to the incident this alert belongs to
    incident_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("incidents.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    # Optional link to the feed that triggered this alert
    feed_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("feeds.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    # Delivery channel (email, sms, call, webhook, …)
    channel: Mapped[str] = mapped_column(String(50), nullable=False, server_default="in_app")
    # Channel-specific delivery address (phone number, email, URL …)
    recipient: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Extra payload / context for rendering the alert
    metadata_: Mapped[dict] = mapped_column(  # type: ignore[type-arg]
        "metadata", JSONB, nullable=False, server_default="{}"
    )
    sent_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    acknowledged_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # ── Relationships ──────────────────────────────────────────────────────
    incident: Mapped["IncidentModel | None"] = relationship(  # type: ignore[name-defined]
        "IncidentModel", back_populates="alerts"
    )
    feed: Mapped["FeedModel | None"] = relationship(  # type: ignore[name-defined]
        "FeedModel", back_populates="alerts"
    )

    __table_args__ = (
        CheckConstraint(
            "severity IN ('critical','high','medium','low','info')",
            name="ck_alerts_severity",
        ),
        CheckConstraint(
            "status IN ('pending','sent','acknowledged','failed','suppressed')",
            name="ck_alerts_status",
        ),
        CheckConstraint(
            "channel IN ('in_app','email','sms','call','webhook','slack')",
            name="ck_alerts_channel",
        ),
        Index("idx_alerts_severity", "severity"),
        Index("idx_alerts_status", "status"),
        Index("idx_alerts_created_at", "created_at"),
    )
