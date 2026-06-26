"""ORM model for the ``feeds`` table.

A Feed is a data ingestion source (e.g. sensor stream, log pipeline, webhook)
whose events are processed by the Overseer AI to generate incidents and alerts.
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, Index, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.infrastructure.db.models.base import Base


class FeedModel(Base):
    __tablename__ = "feeds"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, server_default=func.uuid_generate_v4()
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    source_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="active"
    )
    endpoint_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    config: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default="{}")  # type: ignore[type-arg]
    is_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    last_ingested_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # ── Relationships ──────────────────────────────────────────────────────
    incidents: Mapped[list["IncidentModel"]] = relationship(  # type: ignore[name-defined]
        "IncidentModel", back_populates="feed"
    )
    alerts: Mapped[list["AlertModel"]] = relationship(  # type: ignore[name-defined]
        "AlertModel", back_populates="feed"
    )

    __table_args__ = (
        CheckConstraint(
            "status IN ('active','paused','error','disabled')",
            name="ck_feeds_status",
        ),
        CheckConstraint(
            "source_type IN ('webhook','polling','stream','manual')",
            name="ck_feeds_source_type",
        ),
        Index("idx_feeds_status", "status"),
        Index("idx_feeds_source_type", "source_type"),
    )
