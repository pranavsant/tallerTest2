-- ─────────────────────────────────────────────────────────────────────────────
-- Overseer AI — Initial Schema
-- Migration: 001_initial_schema
-- ─────────────────────────────────────────────────────────────────────────────

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

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

-- ── updated_at auto-update trigger ───────────────────────────────────────────
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS agents_updated_at ON agents;
CREATE TRIGGER agents_updated_at
    BEFORE UPDATE ON agents
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
