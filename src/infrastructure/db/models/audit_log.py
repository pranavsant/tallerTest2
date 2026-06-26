"""ORM model for the ``audit_logs`` table.

Audit logs record every significant state-changing action in the system
(who did what to which entity, when). They are append-only: rows are
never updated or deleted.
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, Text, func
from sqlalchemy.dialects.postgresql import INET, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.infrastructure.db.models.base import Base


class AuditLogModel(Base):
    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, server_default=func.uuid_generate_v4()
    )
    # Who performed the action (NULL = system/automated)
    actor_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    # The type of entity that was acted upon (e.g. 'incident', 'agent', 'feed')
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    # The UUID (as text) of the acted-upon entity
    entity_id: Mapped[str] = mapped_column(Text, nullable=False)
    # Verb describing what happened (e.g. 'created', 'status_changed', 'deleted')
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    # Snapshot of changes: {"before": {...}, "after": {...}}
    diff: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default="{}")  # type: ignore[type-arg]
    # Request context
    ip_address: Mapped[str | None] = mapped_column(INET, nullable=True)
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # ── Relationships ──────────────────────────────────────────────────────
    actor: Mapped["UserModel | None"] = relationship(  # type: ignore[name-defined]
        "UserModel", back_populates="audit_logs"
    )

    __table_args__ = (
        Index("idx_audit_logs_entity_type_id", "entity_type", "entity_id"),
        Index("idx_audit_logs_actor_id", "actor_id"),
        Index("idx_audit_logs_created_at", "created_at"),
        Index("idx_audit_logs_action", "action"),
    )
