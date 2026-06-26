-- ─────────────────────────────────────────────────────────────────────────────
-- Overseer AI — Core Oversight Entities
-- Migration: 002_core_entities
--
-- Adds: users, feeds, incidents, alerts, call_logs, audit_logs
--
-- Prerequisites: 001_initial_schema (agents, sessions, messages, calls)
-- ─────────────────────────────────────────────────────────────────────────────

-- ── users ─────────────────────────────────────────────────────────────────────
-- Application-level user profiles. Authentication identity is managed by
-- Supabase Auth (or another IdP); this table stores enriched profile data
-- linked by the external user UUID.
CREATE TABLE IF NOT EXISTS users (
    id              UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    email           TEXT        NOT NULL UNIQUE,
    full_name       TEXT,
    role            TEXT        NOT NULL DEFAULT 'operator'
                                CHECK (role IN ('admin','operator','viewer')),
    is_active       BOOLEAN     NOT NULL DEFAULT TRUE,
    avatar_url      TEXT,
    last_login_at   TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_users_email     ON users (email);
CREATE INDEX IF NOT EXISTS idx_users_role      ON users (role);
CREATE INDEX IF NOT EXISTS idx_users_is_active ON users (is_active);

DROP TRIGGER IF EXISTS users_updated_at ON users;
CREATE TRIGGER users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ── feeds ─────────────────────────────────────────────────────────────────────
-- A Feed is a data ingestion source (webhook, polling endpoint, stream,
-- or manual entry) whose events are processed to generate incidents & alerts.
CREATE TABLE IF NOT EXISTS feeds (
    id                  UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    name                TEXT        NOT NULL,
    source_type         TEXT        NOT NULL
                                    CHECK (source_type IN ('webhook','polling','stream','manual')),
    status              TEXT        NOT NULL DEFAULT 'active'
                                    CHECK (status IN ('active','paused','error','disabled')),
    endpoint_url        TEXT,
    config              JSONB       NOT NULL DEFAULT '{}',
    is_enabled          BOOLEAN     NOT NULL DEFAULT TRUE,
    last_ingested_at    TIMESTAMPTZ,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_feeds_status      ON feeds (status);
CREATE INDEX IF NOT EXISTS idx_feeds_source_type ON feeds (source_type);
CREATE INDEX IF NOT EXISTS idx_feeds_is_enabled  ON feeds (is_enabled);

DROP TRIGGER IF EXISTS feeds_updated_at ON feeds;
CREATE TRIGGER feeds_updated_at
    BEFORE UPDATE ON feeds
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ── incidents ─────────────────────────────────────────────────────────────────
-- An Incident is a detected anomaly or event requiring investigation.
CREATE TABLE IF NOT EXISTS incidents (
    id           UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    title        TEXT        NOT NULL,
    description  TEXT,
    severity     TEXT        NOT NULL DEFAULT 'medium'
                             CHECK (severity IN ('critical','high','medium','low','info')),
    status       TEXT        NOT NULL DEFAULT 'open'
                             CHECK (status IN ('open','investigating','resolved','closed','false_positive')),
    feed_id      UUID        REFERENCES feeds (id) ON DELETE SET NULL,
    assignee_id  UUID        REFERENCES users (id) ON DELETE SET NULL,
    metadata     JSONB       NOT NULL DEFAULT '{}',
    resolved_at  TIMESTAMPTZ,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_incidents_severity    ON incidents (severity);
CREATE INDEX IF NOT EXISTS idx_incidents_status      ON incidents (status);
CREATE INDEX IF NOT EXISTS idx_incidents_feed_id     ON incidents (feed_id);
CREATE INDEX IF NOT EXISTS idx_incidents_assignee_id ON incidents (assignee_id);
CREATE INDEX IF NOT EXISTS idx_incidents_created_at  ON incidents (created_at);

DROP TRIGGER IF EXISTS incidents_updated_at ON incidents;
CREATE TRIGGER incidents_updated_at
    BEFORE UPDATE ON incidents
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ── alerts ────────────────────────────────────────────────────────────────────
-- An Alert is a notification generated from a Feed event or Incident that
-- may trigger an automated or human response.
CREATE TABLE IF NOT EXISTS alerts (
    id               UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    title            TEXT        NOT NULL,
    message          TEXT,
    severity         TEXT        NOT NULL DEFAULT 'medium'
                                 CHECK (severity IN ('critical','high','medium','low','info')),
    status           TEXT        NOT NULL DEFAULT 'pending'
                                 CHECK (status IN ('pending','sent','acknowledged','failed','suppressed')),
    incident_id      UUID        REFERENCES incidents (id) ON DELETE SET NULL,
    feed_id          UUID        REFERENCES feeds (id) ON DELETE SET NULL,
    channel          TEXT        NOT NULL DEFAULT 'in_app'
                                 CHECK (channel IN ('in_app','email','sms','call','webhook','slack')),
    recipient        TEXT,
    metadata         JSONB       NOT NULL DEFAULT '{}',
    sent_at          TIMESTAMPTZ,
    acknowledged_at  TIMESTAMPTZ,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_alerts_severity    ON alerts (severity);
CREATE INDEX IF NOT EXISTS idx_alerts_status      ON alerts (status);
CREATE INDEX IF NOT EXISTS idx_alerts_incident_id ON alerts (incident_id);
CREATE INDEX IF NOT EXISTS idx_alerts_feed_id     ON alerts (feed_id);
CREATE INDEX IF NOT EXISTS idx_alerts_created_at  ON alerts (created_at);

DROP TRIGGER IF EXISTS alerts_updated_at ON alerts;
CREATE TRIGGER alerts_updated_at
    BEFORE UPDATE ON alerts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ── call_logs ─────────────────────────────────────────────────────────────────
-- AI-enriched records of telephony calls: transcript, sentiment, and
-- structured extracted data. Always linked to a row in the calls table.
CREATE TABLE IF NOT EXISTS call_logs (
    id                 UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    call_id            UUID        NOT NULL REFERENCES calls (id) ON DELETE CASCADE,
    transcript         TEXT,
    summary            TEXT,
    sentiment_score    NUMERIC(5,4)
                       CHECK (sentiment_score IS NULL OR sentiment_score BETWEEN -1 AND 1),
    sentiment_label    TEXT,
    extracted_data     JSONB       NOT NULL DEFAULT '{}',
    processing_status  TEXT        NOT NULL DEFAULT 'pending'
                                   CHECK (processing_status IN ('pending','processing','completed','failed')),
    created_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at         TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_call_logs_call_id           ON call_logs (call_id);
CREATE INDEX IF NOT EXISTS idx_call_logs_processing_status ON call_logs (processing_status);
CREATE INDEX IF NOT EXISTS idx_call_logs_created_at        ON call_logs (created_at);

DROP TRIGGER IF EXISTS call_logs_updated_at ON call_logs;
CREATE TRIGGER call_logs_updated_at
    BEFORE UPDATE ON call_logs
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ── audit_logs ────────────────────────────────────────────────────────────────
-- Append-only audit trail recording every significant state-changing action.
-- Rows are NEVER updated or deleted.
CREATE TABLE IF NOT EXISTS audit_logs (
    id           UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    actor_id     UUID        REFERENCES users (id) ON DELETE SET NULL,
    entity_type  TEXT        NOT NULL,
    entity_id    TEXT        NOT NULL,
    action       TEXT        NOT NULL,
    diff         JSONB       NOT NULL DEFAULT '{}',
    ip_address   INET,
    user_agent   TEXT,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_audit_logs_entity     ON audit_logs (entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_actor_id   ON audit_logs (actor_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at ON audit_logs (created_at);
CREATE INDEX IF NOT EXISTS idx_audit_logs_action     ON audit_logs (action);
