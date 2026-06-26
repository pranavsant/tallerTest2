"""ORM model for the ``call_logs`` table.

A CallLog is an AI-enriched record of a telephony call: transcript,
sentiment, summary, and any extracted structured data. It is always
linked to a row in the ``calls`` table (raw Twilio record).
"""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Numeric, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.infrastructure.db.models.base import Base


class CallLogModel(Base):
    __tablename__ = "call_logs"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, server_default=func.uuid_generate_v4()
    )
    call_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("calls.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # Full transcript of the call in plain text
    transcript: Mapped[str | None] = mapped_column(Text, nullable=True)
    # AI-generated summary
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Overall sentiment score in [-1.0, 1.0]
    sentiment_score: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 4), nullable=True
    )
    # Dominant sentiment label
    sentiment_label: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Structured entities / key facts extracted from the transcript
    extracted_data: Mapped[dict] = mapped_column(  # type: ignore[type-arg]
        JSONB, nullable=False, server_default="{}"
    )
    # Processing status for async enrichment pipeline
    processing_status: Mapped[str] = mapped_column(
        Text, nullable=False, server_default="pending"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # ── Relationships ──────────────────────────────────────────────────────
    call: Mapped["CallModel"] = relationship(  # type: ignore[name-defined]
        "CallModel", back_populates="call_logs"
    )

    __table_args__ = (
        CheckConstraint(
            "sentiment_score IS NULL OR (sentiment_score BETWEEN -1 AND 1)",
            name="ck_call_logs_sentiment_score",
        ),
        CheckConstraint(
            "processing_status IN ('pending','processing','completed','failed')",
            name="ck_call_logs_processing_status",
        ),
        Index("idx_call_logs_created_at", "created_at"),
        Index("idx_call_logs_processing_status", "processing_status"),
    )
