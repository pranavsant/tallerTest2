"""Raw feed items — ingestion pipeline table.

Adds ``raw_feed_items``: normalised, deduplicated units of feed content queued
for downstream AI analysis. Deduplication is enforced by a UNIQUE constraint on
``(feed_id, content_hash)``.

Revision ID: 0002
Revises: 0001
Create Date: 2024-01-02 00:00:00.000000
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


_UP_SQL = """
-- ── raw_feed_items ──────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS raw_feed_items (
    id              UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    feed_id         UUID        NOT NULL REFERENCES feeds (id) ON DELETE CASCADE,
    content_hash    VARCHAR(64) NOT NULL,
    external_id     TEXT,
    title           TEXT,
    content         TEXT,
    url             TEXT,
    published_at    TIMESTAMPTZ,
    raw             JSONB       NOT NULL DEFAULT '{}',
    status          TEXT        NOT NULL DEFAULT 'pending'
                                CHECK (status IN ('pending','processing','analyzed','failed')),
    error           TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_raw_feed_items_feed_content_hash UNIQUE (feed_id, content_hash)
);

CREATE INDEX IF NOT EXISTS idx_raw_feed_items_feed_id    ON raw_feed_items (feed_id);
CREATE INDEX IF NOT EXISTS idx_raw_feed_items_status     ON raw_feed_items (status);
CREATE INDEX IF NOT EXISTS idx_raw_feed_items_created_at ON raw_feed_items (created_at);
"""

_DOWN_SQL = """
DROP TABLE IF EXISTS raw_feed_items CASCADE;
"""


def upgrade() -> None:
    op.execute(_UP_SQL)


def downgrade() -> None:
    op.execute(_DOWN_SQL)
