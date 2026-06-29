# Overseer AI — Database Schema

> **Engine:** PostgreSQL 16  
> **Extensions:** `uuid-ossp` (UUID generation)  
> **Migration tools:**  
>   - **Alembic** (canonical) — `alembic upgrade head`  
>   - **Custom asyncpg runner** (legacy) — `python -m migrations.run`

---

## Table of Contents

1. [agents](#agents)
2. [sessions](#sessions)
3. [messages](#messages)
4. [calls](#calls)
5. [users](#users)
6. [feeds](#feeds)
6a. [raw_feed_items](#raw_feed_items)
7. [incidents](#incidents)
8. [alerts](#alerts)
9. [call_logs](#call_logs)
10. [audit_logs](#audit_logs)
11. [Relationships diagram](#relationships-diagram)
12. [Index summary](#index-summary)
13. [Triggers](#triggers)
14. [Migration files](#migration-files)

---

## agents

AI agent personas. Each agent has a voice (ElevenLabs), a system prompt, and
a lifecycle status that controls whether it can accept new sessions.

| Column | Type | Nullable | Default | Notes |
|---|---|---|---|---|
| `id` | `UUID` | NO | `uuid_generate_v4()` | PK |
| `name` | `TEXT` | NO | — | 1–100 chars |
| `system_prompt` | `TEXT` | NO | — | ≤ 8 000 chars (app-enforced) |
| `status` | `TEXT` | NO | `'idle'` | `idle \| active \| busy \| offline \| suspended` |
| `voice_id` | `TEXT` | NO | — | ElevenLabs voice ID |
| `model_id` | `TEXT` | NO | `'eleven_turbo_v2'` | ElevenLabs model ID |
| `stability` | `NUMERIC(4,3)` | NO | `0.500` | `[0, 1]` |
| `similarity_boost` | `NUMERIC(4,3)` | NO | `0.750` | `[0, 1]` |
| `style` | `NUMERIC(4,3)` | NO | `0.000` | `[0, 1]` |
| `use_speaker_boost` | `BOOLEAN` | NO | `TRUE` | |
| `created_at` | `TIMESTAMPTZ` | NO | `NOW()` | |
| `updated_at` | `TIMESTAMPTZ` | NO | `NOW()` | Auto-updated by trigger |

**Indexes:** `idx_agents_status (status)`  
**Triggers:** `agents_updated_at` — sets `updated_at = NOW()` on every UPDATE

---

## sessions

A bounded conversation between a user and an agent. Holds the lifecycle and
timing of a single interaction.

| Column | Type | Nullable | Default | Notes |
|---|---|---|---|---|
| `id` | `UUID` | NO | `uuid_generate_v4()` | PK |
| `agent_id` | `UUID` | NO | — | FK → `agents.id` CASCADE DELETE |
| `user_id` | `TEXT` | NO | — | External user identifier |
| `status` | `TEXT` | NO | `'pending'` | `pending \| active \| paused \| completed \| failed` |
| `metadata` | `JSONB` | NO | `'{}'` | Free-form key/value pairs |
| `started_at` | `TIMESTAMPTZ` | YES | — | Set on first ACTIVE transition |
| `ended_at` | `TIMESTAMPTZ` | YES | — | Set on terminal transition |
| `created_at` | `TIMESTAMPTZ` | NO | `NOW()` | |

**Indexes:** `idx_sessions_agent_id`, `idx_sessions_user_id`, `idx_sessions_status`

---

## messages

Individual conversational turns within a session.

| Column | Type | Nullable | Default | Notes |
|---|---|---|---|---|
| `id` | `UUID` | NO | `uuid_generate_v4()` | PK |
| `session_id` | `UUID` | NO | — | FK → `sessions.id` CASCADE DELETE |
| `role` | `TEXT` | NO | — | `user \| agent \| system` |
| `content` | `TEXT` | NO | — | ≤ 32 000 chars (app-enforced) |
| `audio_url` | `TEXT` | YES | — | URL to synthesised audio file |
| `created_at` | `TIMESTAMPTZ` | NO | `NOW()` | |

**Indexes:** `idx_messages_session_id`, `idx_messages_created_at (session_id, created_at)`

---

## calls

Raw Twilio telephony call records. Every outbound call initiated by an agent
produces one row here.

| Column | Type | Nullable | Default | Notes |
|---|---|---|---|---|
| `id` | `UUID` | NO | `uuid_generate_v4()` | PK |
| `agent_id` | `UUID` | NO | — | FK → `agents.id` CASCADE DELETE |
| `session_id` | `UUID` | YES | — | FK → `sessions.id` SET NULL |
| `to_number` | `TEXT` | NO | — | E.164 destination number |
| `from_number` | `TEXT` | NO | — | E.164 Twilio number |
| `twilio_call_sid` | `TEXT` | YES | — | Unique; set by Twilio |
| `status` | `TEXT` | NO | `'queued'` | `queued \| ringing \| in-progress \| completed \| failed \| no-answer \| busy \| canceled` |
| `recording_url` | `TEXT` | YES | — | Twilio recording URL |
| `started_at` | `TIMESTAMPTZ` | YES | — | |
| `ended_at` | `TIMESTAMPTZ` | YES | — | |
| `created_at` | `TIMESTAMPTZ` | NO | `NOW()` | |

**Indexes:** `idx_calls_agent_id`, `idx_calls_twilio_call_sid (UNIQUE)`, `idx_calls_status`

---

## users

Application-level operator profiles. Authentication identity is managed by
Supabase Auth (or another IdP); the `id` matches the Supabase user UUID.

| Column | Type | Nullable | Default | Notes |
|---|---|---|---|---|
| `id` | `UUID` | NO | `uuid_generate_v4()` | PK; matches Supabase auth UUID |
| `email` | `TEXT` | NO | — | UNIQUE; max 320 chars |
| `full_name` | `TEXT` | YES | — | |
| `role` | `TEXT` | NO | `'operator'` | `admin \| operator \| viewer` |
| `is_active` | `BOOLEAN` | NO | `TRUE` | Soft-disable without deleting |
| `avatar_url` | `TEXT` | YES | — | |
| `last_login_at` | `TIMESTAMPTZ` | YES | — | Set on successful login |
| `created_at` | `TIMESTAMPTZ` | NO | `NOW()` | |
| `updated_at` | `TIMESTAMPTZ` | NO | `NOW()` | Auto-updated by trigger |

**Indexes:** `idx_users_email (UNIQUE)`, `idx_users_role`, `idx_users_is_active`  
**Triggers:** `users_updated_at`

---

## feeds

Data ingestion sources whose events are processed into incidents and alerts.

| Column | Type | Nullable | Default | Notes |
|---|---|---|---|---|
| `id` | `UUID` | NO | `uuid_generate_v4()` | PK |
| `name` | `TEXT` | NO | — | Human-readable label |
| `source_type` | `TEXT` | NO | — | `webhook \| polling \| stream \| manual` |
| `status` | `TEXT` | NO | `'active'` | `active \| paused \| error \| disabled` |
| `endpoint_url` | `TEXT` | YES | — | Source URL (polling/webhook) |
| `config` | `JSONB` | NO | `'{}'` | Source-specific configuration |
| `is_enabled` | `BOOLEAN` | NO | `TRUE` | Quick on/off toggle |
| `last_ingested_at` | `TIMESTAMPTZ` | YES | — | Timestamp of most recent event |
| `created_at` | `TIMESTAMPTZ` | NO | `NOW()` | |
| `updated_at` | `TIMESTAMPTZ` | NO | `NOW()` | Auto-updated by trigger |

**Indexes:** `idx_feeds_status`, `idx_feeds_source_type`, `idx_feeds_is_enabled`  
**Triggers:** `feeds_updated_at`

> **Reserved `config` keys** (managed by the app, lifted out into the `Feed`
> entity rather than exposed as raw config): `polling_interval_seconds`
> (poll cadence), `_consecutive_failures` and `_last_error` (ingestion backoff
> bookkeeping), and `format` / `items_path` / `field_map` / `headers` (consumed
> by the polling fetchers to parse RSS/Atom vs JSON-API sources).

---

## raw_feed_items

Normalised, deduplicated units of content ingested from a Feed by the
background ingestion worker. Every row is queued for downstream AI analysis;
`status` tracks its progress through that pipeline. Re-ingesting the same
underlying item is a no-op, enforced by the `(feed_id, content_hash)` UNIQUE
constraint.

| Column | Type | Nullable | Default | Notes |
|---|---|---|---|---|
| `id` | `UUID` | NO | `uuid_generate_v4()` | PK |
| `feed_id` | `UUID` | NO | — | FK → `feeds.id` CASCADE DELETE |
| `content_hash` | `VARCHAR(64)` | NO | — | SHA-256 dedup digest (feed-scoped) |
| `external_id` | `TEXT` | YES | — | Source's own item identifier, if any |
| `title` | `TEXT` | YES | — | Normalised headline |
| `content` | `TEXT` | YES | — | Normalised body/payload text |
| `url` | `TEXT` | YES | — | Canonical link back to the source item |
| `published_at` | `TIMESTAMPTZ` | YES | — | Source-reported publish time |
| `raw` | `JSONB` | NO | `'{}'` | Untouched source payload (for re-processing) |
| `status` | `TEXT` | NO | `'pending'` | `pending \| processing \| analyzed \| failed` |
| `error` | `TEXT` | YES | — | Reason analysis failed, if it failed |
| `created_at` | `TIMESTAMPTZ` | NO | `NOW()` | |

**Constraints:** `uq_raw_feed_items_feed_content_hash UNIQUE (feed_id, content_hash)`  
**Indexes:** `idx_raw_feed_items_feed_id`, `idx_raw_feed_items_status`, `idx_raw_feed_items_created_at`  
> Append-mostly: rows are inserted on ingest and only their `status`/`error`
> change as the AI-analysis stage processes them. No `updated_at` trigger.

---

## incidents

Detected anomalies or events requiring human or AI-assisted investigation.

| Column | Type | Nullable | Default | Notes |
|---|---|---|---|---|
| `id` | `UUID` | NO | `uuid_generate_v4()` | PK |
| `title` | `TEXT` | NO | — | Short summary |
| `description` | `TEXT` | YES | — | Full detail |
| `severity` | `TEXT` | NO | `'medium'` | `critical \| high \| medium \| low \| info` |
| `status` | `TEXT` | NO | `'open'` | `open \| investigating \| resolved \| closed \| false_positive` |
| `feed_id` | `UUID` | YES | — | FK → `feeds.id` SET NULL |
| `assignee_id` | `UUID` | YES | — | FK → `users.id` SET NULL |
| `metadata` | `JSONB` | NO | `'{}'` | Tags, source refs, raw payload excerpt |
| `resolved_at` | `TIMESTAMPTZ` | YES | — | Set when status → `resolved` |
| `created_at` | `TIMESTAMPTZ` | NO | `NOW()` | |
| `updated_at` | `TIMESTAMPTZ` | NO | `NOW()` | Auto-updated by trigger |

**Indexes:** `idx_incidents_severity`, `idx_incidents_status`, `idx_incidents_feed_id`,  
`idx_incidents_assignee_id`, `idx_incidents_created_at`  
**Triggers:** `incidents_updated_at`

---

## alerts

Notifications generated from feed events or incidents that may trigger
automated or human responses.

| Column | Type | Nullable | Default | Notes |
|---|---|---|---|---|
| `id` | `UUID` | NO | `uuid_generate_v4()` | PK |
| `title` | `TEXT` | NO | — | |
| `message` | `TEXT` | YES | — | Longer body text |
| `severity` | `TEXT` | NO | `'medium'` | `critical \| high \| medium \| low \| info` |
| `status` | `TEXT` | NO | `'pending'` | `pending \| sent \| acknowledged \| failed \| suppressed` |
| `incident_id` | `UUID` | YES | — | FK → `incidents.id` SET NULL |
| `feed_id` | `UUID` | YES | — | FK → `feeds.id` SET NULL |
| `channel` | `TEXT` | NO | `'in_app'` | `in_app \| email \| sms \| call \| webhook \| slack` |
| `recipient` | `TEXT` | YES | — | Channel-specific address |
| `metadata` | `JSONB` | NO | `'{}'` | Channel payload / context |
| `sent_at` | `TIMESTAMPTZ` | YES | — | Set when delivered |
| `acknowledged_at` | `TIMESTAMPTZ` | YES | — | Set when operator acks |
| `created_at` | `TIMESTAMPTZ` | NO | `NOW()` | |
| `updated_at` | `TIMESTAMPTZ` | NO | `NOW()` | Auto-updated by trigger |

**Indexes:** `idx_alerts_severity`, `idx_alerts_status`, `idx_alerts_incident_id`,  
`idx_alerts_feed_id`, `idx_alerts_created_at`  
**Triggers:** `alerts_updated_at`

---

## call_logs

AI-enriched records of telephony calls: transcript, sentiment analysis, and
structured data extracted from the conversation. One-to-many with `calls`.

| Column | Type | Nullable | Default | Notes |
|---|---|---|---|---|
| `id` | `UUID` | NO | `uuid_generate_v4()` | PK |
| `call_id` | `UUID` | NO | — | FK → `calls.id` CASCADE DELETE |
| `transcript` | `TEXT` | YES | — | Full conversation text |
| `summary` | `TEXT` | YES | — | AI-generated summary |
| `sentiment_score` | `NUMERIC(5,4)` | YES | — | `[-1.0, 1.0]`; NULL if not yet analysed |
| `sentiment_label` | `TEXT` | YES | — | e.g. `positive`, `negative`, `neutral` |
| `extracted_data` | `JSONB` | NO | `'{}'` | Entities / key facts extracted from transcript |
| `processing_status` | `TEXT` | NO | `'pending'` | `pending \| processing \| completed \| failed` |
| `created_at` | `TIMESTAMPTZ` | NO | `NOW()` | |
| `updated_at` | `TIMESTAMPTZ` | NO | `NOW()` | Auto-updated by trigger |

**Indexes:** `idx_call_logs_call_id`, `idx_call_logs_processing_status`, `idx_call_logs_created_at`  
**Triggers:** `call_logs_updated_at`

---

## audit_logs

Append-only audit trail. Records every significant state-changing action:
who did what, to which entity, when. Rows are **never** updated or deleted.

| Column | Type | Nullable | Default | Notes |
|---|---|---|---|---|
| `id` | `UUID` | NO | `uuid_generate_v4()` | PK |
| `actor_id` | `UUID` | YES | — | FK → `users.id` SET NULL; NULL = automated/system |
| `entity_type` | `TEXT` | NO | — | e.g. `incident`, `agent`, `feed` |
| `entity_id` | `TEXT` | NO | — | UUID (as text) of the acted-upon row |
| `action` | `TEXT` | NO | — | e.g. `created`, `status_changed`, `deleted` |
| `diff` | `JSONB` | NO | `'{}'` | `{"before": {...}, "after": {...}}` |
| `ip_address` | `INET` | YES | — | Client IP address |
| `user_agent` | `TEXT` | YES | — | Client User-Agent header |
| `created_at` | `TIMESTAMPTZ` | NO | `NOW()` | Immutable insert timestamp |

**Indexes:** `idx_audit_logs_entity (entity_type, entity_id)`, `idx_audit_logs_actor_id`,  
`idx_audit_logs_created_at`, `idx_audit_logs_action`  
> No `updated_at` — this table is append-only.

---

## Relationships diagram

```
agents ──────────────────────────── sessions
  │                                     │
  │  (CASCADE DELETE)          (CASCADE DELETE)
  │                                     │
  └── calls ──────────── call_logs     messages
           (CASCADE)
           (SET NULL → sessions)

users ──── incidents ──── alerts
  │             │             │
  │          feeds ───────────┘
  │
  └── audit_logs  (actor_id, SET NULL)

feeds ──── incidents
feeds ──── alerts
incidents ──── alerts
calls ──── call_logs
```

---

## Index summary

| Table | Index | Columns |
|---|---|---|
| `agents` | `idx_agents_status` | `status` |
| `sessions` | `idx_sessions_agent_id` | `agent_id` |
| `sessions` | `idx_sessions_user_id` | `user_id` |
| `sessions` | `idx_sessions_status` | `status` |
| `messages` | `idx_messages_session_id` | `session_id` |
| `messages` | `idx_messages_created_at` | `(session_id, created_at)` |
| `calls` | `idx_calls_agent_id` | `agent_id` |
| `calls` | `idx_calls_twilio_call_sid` | `twilio_call_sid` (UNIQUE) |
| `calls` | `idx_calls_status` | `status` |
| `users` | `idx_users_email` | `email` (UNIQUE) |
| `users` | `idx_users_role` | `role` |
| `users` | `idx_users_is_active` | `is_active` |
| `feeds` | `idx_feeds_status` | `status` |
| `feeds` | `idx_feeds_source_type` | `source_type` |
| `feeds` | `idx_feeds_is_enabled` | `is_enabled` |
| `raw_feed_items` | `idx_raw_feed_items_feed_id` | `feed_id` |
| `raw_feed_items` | `idx_raw_feed_items_status` | `status` |
| `raw_feed_items` | `idx_raw_feed_items_created_at` | `created_at` |
| `raw_feed_items` | `uq_raw_feed_items_feed_content_hash` | `(feed_id, content_hash)` (UNIQUE) |
| `incidents` | `idx_incidents_severity` | `severity` |
| `incidents` | `idx_incidents_status` | `status` |
| `incidents` | `idx_incidents_feed_id` | `feed_id` |
| `incidents` | `idx_incidents_assignee_id` | `assignee_id` |
| `incidents` | `idx_incidents_created_at` | `created_at` |
| `alerts` | `idx_alerts_severity` | `severity` |
| `alerts` | `idx_alerts_status` | `status` |
| `alerts` | `idx_alerts_incident_id` | `incident_id` |
| `alerts` | `idx_alerts_feed_id` | `feed_id` |
| `alerts` | `idx_alerts_created_at` | `created_at` |
| `call_logs` | `idx_call_logs_call_id` | `call_id` |
| `call_logs` | `idx_call_logs_processing_status` | `processing_status` |
| `call_logs` | `idx_call_logs_created_at` | `created_at` |
| `audit_logs` | `idx_audit_logs_entity` | `(entity_type, entity_id)` |
| `audit_logs` | `idx_audit_logs_actor_id` | `actor_id` |
| `audit_logs` | `idx_audit_logs_created_at` | `created_at` |
| `audit_logs` | `idx_audit_logs_action` | `action` |

---

## Triggers

All mutable tables (except `audit_logs` and `messages`) have a
`BEFORE UPDATE` trigger that automatically sets `updated_at = NOW()`.

```sql
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
```

Tables with the trigger: `agents`, `users`, `feeds`, `incidents`, `alerts`,
`call_logs`.

---

## Migration files

### Custom asyncpg runner (`migrations/`)

| File | Description |
|---|---|
| `001_initial_schema.sql` | `agents`, `sessions`, `messages`, `calls` |
| `002_core_entities.sql` | `users`, `feeds`, `incidents`, `alerts`, `call_logs`, `audit_logs` |
| `003_raw_feed_items.sql` | `raw_feed_items` (feed ingestion pipeline) |

Run with:
```bash
python -m migrations.run
```

### Alembic (`alembic/`)

| Revision | File | Description |
|---|---|---|
| `0001` | `alembic/versions/0001_initial_schema.py` | Full schema (all 10 tables) |
| `0002` | `alembic/versions/0002_raw_feed_items.py` | `raw_feed_items` (feed ingestion pipeline) |

Run with:
```bash
alembic upgrade head    # apply all pending migrations
alembic downgrade -1    # roll back one revision
alembic current         # show current revision
alembic history         # list all revisions
```

> **Note:** Both migration systems are kept in sync. If you add a table, create
> both a new numbered `.sql` file and a new Alembic revision.
