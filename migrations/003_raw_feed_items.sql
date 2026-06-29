-- ─────────────────────────────────────────────────────────────────────────────
-- Overseer AI — Raw Feed Items (ingestion pipeline)
-- Migration: 003_raw_feed_items
--
-- Adds: raw_feed_items
--
-- Prerequisites: 002_core_entities (feeds)
-- ─────────────────────────────────────────────────────────────────────────────

-- ── raw_feed_items ──────────────────────────────────────────────────────────
-- A RawFeedItem is a single unit of content pulled from a Feed source and
-- normalised into the platform's standard schema. Every row is queued for
-- downstream AI analysis; `status` tracks its progress through the pipeline.
--
-- Deduplication: the UNIQUE (feed_id, content_hash) constraint makes
-- re-ingesting the same underlying item a no-op.
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
