"""ORM model for the ``users`` table.

Stores application-level user profiles. Authentication identity is managed
by Supabase Auth; this table holds the enriched profile data linked by
the Supabase user UUID.
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, Index, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.infrastructure.db.models.base import Base


class UserModel(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        server_default=func.uuid_generate_v4(),
        comment="Matches the Supabase Auth user UUID when Supabase is in use.",
    )
    email: Mapped[str] = mapped_column(
        String(320), nullable=False, unique=True, index=True
    )
    full_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    # Local mirror of the user's application role. The authoritative source for
    # authorization is the role in the user's Supabase ``app_metadata`` (it is
    # stamped onto the access token and enforced via ``require_role``). This
    # column exists for profile display/reporting and stays in sync when roles
    # are assigned through the admin panel.
    role: Mapped[str] = mapped_column(
        String(30), nullable=False, server_default="operator"
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    avatar_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_login_at: Mapped[datetime | None] = mapped_column(
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
        "IncidentModel",
        back_populates="assignee",
        foreign_keys="IncidentModel.assignee_id",
    )
    audit_logs: Mapped[list["AuditLogModel"]] = relationship(  # type: ignore[name-defined]
        "AuditLogModel", back_populates="actor"
    )

    __table_args__ = (
        CheckConstraint(
            "role IN ('admin','operator','viewer')", name="ck_users_role"
        ),
        Index("idx_users_role", "role"),
    )
