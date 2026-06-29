"""ORM model for the ``raw_feed_items`` table.

A RawFeedItem is a single unit of content pulled from a Feed source and
normalised into the platform's standard schema. Every row is queued for
downstream AI analysis; ``status`` tracks its progress through that pipeline.

Deduplication is enforced at the database level by a UNIQUE constraint on
``(feed_id, content_hash)`` — re-ingesting the same underlying item is a no-op.
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.infrastructure.db.models.base import Base


class RawFeedItemModel(Base):
    __tablename__ = "raw_feed_items"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, server_default=func.uuid_generate_v4()
    )
    feed_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("feeds.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # Stable SHA-256 dedup digest, scoped to feed_id by the unique constraint.
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    # The source's own identifier for the item, when one exists.
    external_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    title: Mapped[str | None] = mapped_column(Text, nullable=True)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    url: Mapped[str | None] = mapped_column(Text, nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    # Untouched source payload, retained for re-processing.
    raw: Mapped[dict] = mapped_column(  # type: ignore[type-arg]
        JSONB, nullable=False, server_default="{}"
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="pending"
    )
    # Reason analysis failed, if it failed.
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # ── Relationships ──────────────────────────────────────────────────────
    feed: Mapped["FeedModel"] = relationship(  # type: ignore[name-defined]
        "FeedModel", back_populates="raw_items"
    )

    __table_args__ = (
        UniqueConstraint(
            "feed_id", "content_hash", name="uq_raw_feed_items_feed_content_hash"
        ),
        CheckConstraint(
            "status IN ('pending','processing','analyzed','failed')",
            name="ck_raw_feed_items_status",
        ),
        Index("idx_raw_feed_items_feed_id", "feed_id"),
        Index("idx_raw_feed_items_status", "status"),
        Index("idx_raw_feed_items_created_at", "created_at"),
    )
