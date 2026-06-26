"""Initial schema — all core tables.

Creates the complete database schema for Overseer AI:
  - agents, sessions, messages, calls          (AI agent pipeline)
  - users                                       (operator profiles)
  - feeds, incidents, alerts                    (event / oversight domain)
  - call_logs                                   (AI-enriched call records)
  - audit_logs                                  (append-only audit trail)

Revision ID: 0001
Revises:
Create Date: 2024-01-01 00:00:00.000000
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_UP_SQL = """
-- ─────────────────────────────────────────────────────────────────────────────
-- Overseer AI — Full Schema (Alembic revision 0001)
-- ─────────────────────────────────────────────────────────────────────────────

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ── updated_at auto-update trigger function ───────────────────────────────────
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ── agents ───────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS agents (
    id                UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    name              TEXT        NOT NULL CHECK (char_length(name) BETWEEN 1 AND 100),
    system_prompt     TEXT        NOT NULL,
    status            TEXT        NOT NULL DEFAULT 'idle'
                                  CHECK (status IN ('idle','active','busy','offline','suspended')),
    voice_id          TEXT        NOT NULL,
    model_id          TEXT        NOT NULL DEFAULT 'eleven_turbo_v2',
    stability         NUMERIC(4,3) NOT NULL DEFAULT 0.500 CHECK (stability BETWEEN 0 AND 1),
    similarity_boost  NUMERIC(4,3) NOT NULL DEFAULT 0.750 CHECK (similarity_boost BETWEEN 0 AND 1),
    style             NUMERIC(4,3) NOT NULL DEFAULT 0.000 CHECK (style BETWEEN 0 AND 1),
    use_speaker_boost BOOLEAN     NOT NULL DEFAULT TRUE,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_agents_status ON agents (status);

DROP TRIGGER IF EXISTS agents_updated_at ON agents;
CREATE TRIGGER agents_updated_at
    BEFORE UPDATE ON agents
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ── sessions ─────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS sessions (
    id          UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_id    UUID        NOT NULL REFERENCES agents (id) ON DELETE CASCADE,
    user_id     TEXT        NOT NULL,
    status      TEXT        NOT NULL DEFAULT 'pending'
                            CHECK (status IN ('pending','active','paused','completed','failed')),
    metadata    JSONB       NOT NULL DEFAULT '{}',
    started_at  TIMESTAMPTZ,
    ended_at    TIMESTAMPTZ,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_sessions_agent_id ON sessions (agent_id);
CREATE INDEX IF NOT EXISTS idx_sessions_user_id  ON sessions (user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_status   ON sessions (status);

-- ── messages ─────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS messages (
    id          UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id  UUID        NOT NULL REFERENCES sessions (id) ON DELETE CASCADE,
    role        TEXT        NOT NULL CHECK (role IN ('user','agent','system')),
    content     TEXT        NOT NULL,
    audio_url   TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_messages_session_id ON messages (session_id);
CREATE INDEX IF NOT EXISTS idx_messages_created_at ON messages (session_id, created_at);

-- ── calls ─────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS calls (
    id               UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_id         UUID        NOT NULL REFERENCES agents (id) ON DELETE CASCADE,
    session_id       UUID        REFERENCES sessions (id) ON DELETE SET NULL,
    to_number        TEXT        NOT NULL,
    from_number      TEXT        NOT NULL,
    twilio_call_sid  TEXT        UNIQUE,
    status           TEXT        NOT NULL DEFAULT 'queued'
                                 CHECK (status IN (
                                     'queued','ringing','in-progress',
                                     'completed','failed','no-answer','busy','canceled'
                                 )),
    recording_url    TEXT,
    started_at       TIMESTAMPTZ,
    ended_at         TIMESTAMPTZ,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_calls_agent_id        ON calls (agent_id);
CREATE INDEX IF NOT EXISTS idx_calls_twilio_call_sid ON calls (twilio_call_sid);
CREATE INDEX IF NOT EXISTS idx_calls_status          ON calls (status);

-- ── users ─────────────────────────────────────────────────────────────────────
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

CREATE INDEX IF NOT EXISTS idx_users_email    ON users (email);
CREATE INDEX IF NOT EXISTS idx_users_role     ON users (role);
CREATE INDEX IF NOT EXISTS idx_users_is_active ON users (is_active);

DROP TRIGGER IF EXISTS users_updated_at ON users;
CREATE TRIGGER users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ── feeds ─────────────────────────────────────────────────────────────────────
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

CREATE INDEX IF NOT EXISTS idx_incidents_severity   ON incidents (severity);
CREATE INDEX IF NOT EXISTS idx_incidents_status     ON incidents (status);
CREATE INDEX IF NOT EXISTS idx_incidents_feed_id    ON incidents (feed_id);
CREATE INDEX IF NOT EXISTS idx_incidents_assignee_id ON incidents (assignee_id);
CREATE INDEX IF NOT EXISTS idx_incidents_created_at ON incidents (created_at);

DROP TRIGGER IF EXISTS incidents_updated_at ON incidents;
CREATE TRIGGER incidents_updated_at
    BEFORE UPDATE ON incidents
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ── alerts ────────────────────────────────────────────────────────────────────
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
-- Append-only: no UPDATE or DELETE on this table.
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

CREATE INDEX IF NOT EXISTS idx_audit_logs_entity   ON audit_logs (entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_actor_id ON audit_logs (actor_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at ON audit_logs (created_at);
CREATE INDEX IF NOT EXISTS idx_audit_logs_action   ON audit_logs (action);
"""

_DOWN_SQL = """
DROP TABLE IF EXISTS audit_logs   CASCADE;
DROP TABLE IF EXISTS call_logs    CASCADE;
DROP TABLE IF EXISTS alerts       CASCADE;
DROP TABLE IF EXISTS incidents    CASCADE;
DROP TABLE IF EXISTS feeds        CASCADE;
DROP TABLE IF EXISTS users        CASCADE;
DROP TABLE IF EXISTS calls        CASCADE;
DROP TABLE IF EXISTS messages     CASCADE;
DROP TABLE IF EXISTS sessions     CASCADE;
DROP TABLE IF EXISTS agents       CASCADE;
DROP FUNCTION IF EXISTS update_updated_at_column() CASCADE;
DROP EXTENSION IF EXISTS "uuid-ossp";
"""


def upgrade() -> None:
    op.execute(_UP_SQL)


def downgrade() -> None:
    op.execute(_DOWN_SQL)
