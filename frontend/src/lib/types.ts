/**
 * Shared domain types for the Overseer AI frontend.
 *
 * These interfaces are the canonical, serialized (JSON) shapes returned by the
 * FastAPI backend. Field names are deliberately `snake_case` to match the API
 * responses 1:1 (which in turn mirror the PostgreSQL schema in
 * `migrations/001_initial_schema.sql` and `migrations/002_core_entities.sql`).
 *
 * Conventions
 * -----------
 * - Timestamps are ISO-8601 strings (the backend serializes `datetime` via
 *   `.isoformat()`), not `Date` objects. Parse at the edge if you need a `Date`.
 * - String-literal unions mirror the `CHECK (... IN (...))` constraints in the
 *   schema so invalid states are unrepresentable in the type system.
 * - JSON columns (`metadata`, `config`, `extracted_data`) are typed as
 *   `Record<string, unknown>` — the backend stores free-form JSONB.
 */

// ---------------------------------------------------------------------------
// Primitives
// ---------------------------------------------------------------------------

/** A UUID string (e.g. "3f2504e0-4f89-41d3-9a0c-0305e82c3301"). */
export type UUID = string;

/** An ISO-8601 timestamp string (e.g. "2026-06-26T12:34:56.789+00:00"). */
export type ISODateString = string;

/** Free-form JSONB payload as returned by the API. */
export type JsonObject = Record<string, unknown>;

// ---------------------------------------------------------------------------
// Enums — mirror the PostgreSQL CHECK constraints
// ---------------------------------------------------------------------------

/** Shared severity scale used by incidents and alerts. */
export type Severity = "critical" | "high" | "medium" | "low" | "info";

export type IncidentStatus = "open" | "investigating" | "resolved" | "closed" | "false_positive";

export type AlertStatus = "pending" | "sent" | "acknowledged" | "failed" | "suppressed";

export type AlertChannel = "in_app" | "email" | "sms" | "call" | "webhook" | "slack";

export type FeedStatus = "active" | "paused" | "error" | "disabled";

export type FeedSourceType = "webhook" | "polling" | "stream" | "manual";

export type CallLogProcessingStatus = "pending" | "processing" | "completed" | "failed";

export type AgentStatus = "idle" | "active" | "busy" | "offline" | "suspended";

export type SessionStatus = "pending" | "active" | "paused" | "completed" | "failed";

export type MessageRole = "user" | "agent" | "system";

export type CallStatus =
  | "queued"
  | "ringing"
  | "in-progress"
  | "completed"
  | "failed"
  | "no-answer"
  | "busy"
  | "canceled";

export type UserRole = "admin" | "operator" | "viewer";

// ---------------------------------------------------------------------------
// Core oversight entities (migration 002)
// ---------------------------------------------------------------------------

/**
 * A detected anomaly or event requiring investigation.
 * Table: `incidents`.
 */
export interface Incident {
  id: UUID;
  title: string;
  description: string | null;
  severity: Severity;
  status: IncidentStatus;
  feed_id: UUID | null;
  assignee_id: UUID | null;
  metadata: JsonObject;
  resolved_at: ISODateString | null;
  created_at: ISODateString;
  updated_at: ISODateString;
}

/**
 * A notification generated from a feed event or incident that may trigger an
 * automated or human response.
 * Table: `alerts`.
 */
export interface Alert {
  id: UUID;
  title: string;
  message: string | null;
  severity: Severity;
  status: AlertStatus;
  incident_id: UUID | null;
  feed_id: UUID | null;
  channel: AlertChannel;
  recipient: string | null;
  metadata: JsonObject;
  sent_at: ISODateString | null;
  acknowledged_at: ISODateString | null;
  created_at: ISODateString;
  updated_at: ISODateString;
}

/**
 * A data ingestion source whose events are processed to generate incidents
 * and alerts.
 * Table: `feeds`.
 */
export interface Feed {
  id: UUID;
  name: string;
  source_type: FeedSourceType;
  status: FeedStatus;
  endpoint_url: string | null;
  config: JsonObject;
  is_enabled: boolean;
  last_ingested_at: ISODateString | null;
  created_at: ISODateString;
  updated_at: ISODateString;
}

/**
 * An AI-enriched record of a telephony call: transcript, sentiment, and
 * structured extracted data. Always linked to a row in `calls`.
 * Table: `call_logs`.
 *
 * Note: `sentiment_score` is a `NUMERIC(5,4)` in PostgreSQL; FastAPI/JSON
 * serializes it as a number in the range [-1, 1].
 */
export interface CallLog {
  id: UUID;
  call_id: UUID;
  transcript: string | null;
  summary: string | null;
  sentiment_score: number | null;
  sentiment_label: string | null;
  extracted_data: JsonObject;
  processing_status: CallLogProcessingStatus;
  created_at: ISODateString;
  updated_at: ISODateString;
}

/**
 * Application-level user profile.
 * Table: `users`.
 */
export interface User {
  id: UUID;
  email: string;
  full_name: string | null;
  role: UserRole;
  is_active: boolean;
  avatar_url: string | null;
  last_login_at: ISODateString | null;
  created_at: ISODateString;
  updated_at: ISODateString;
}

// ---------------------------------------------------------------------------
// Conversational / telephony entities (migration 001)
// ---------------------------------------------------------------------------

/**
 * An AI agent. Shape matches the `/agents` API response (`AgentResponse`),
 * which uses `agent_id` rather than the raw `id` column.
 */
export interface Agent {
  agent_id: UUID;
  name: string;
  system_prompt: string;
  status: AgentStatus;
  voice_id: string;
  model_id: string;
  stability: number;
  similarity_boost: number;
  created_at: ISODateString;
  updated_at: ISODateString;
}

/**
 * A conversation session between a user and an agent. Shape matches the
 * `/sessions` API response (`SessionResponse`).
 */
export interface Session {
  session_id: UUID;
  agent_id: UUID;
  user_id: string;
  status: SessionStatus;
  metadata: Record<string, string>;
  started_at: ISODateString | null;
  ended_at: ISODateString | null;
  created_at: ISODateString;
  duration_seconds: number | null;
}

/**
 * A single message within a session. Shape matches the `/messages` API
 * response (`MessageResponse`).
 */
export interface Message {
  message_id: UUID;
  session_id: UUID;
  role: MessageRole;
  content: string;
  audio_url: string | null;
  created_at: ISODateString;
}

/**
 * A telephony call. Shape matches the `/calls` API response (`CallResponse`).
 */
export interface Call {
  call_id: UUID;
  agent_id: UUID;
  session_id: UUID | null;
  to_number: string;
  from_number: string;
  twilio_call_sid: string | null;
  status: CallStatus;
  created_at: ISODateString;
}

// ---------------------------------------------------------------------------
// Request payloads
// ---------------------------------------------------------------------------

export interface CreateAgentInput {
  name: string;
  system_prompt: string;
  voice_id: string;
  model_id?: string;
  stability?: number;
  similarity_boost?: number;
}

export interface ListAgentsParams {
  status?: AgentStatus;
  limit?: number;
  offset?: number;
}

export interface StartSessionInput {
  agent_id: string;
  user_id: string;
  metadata?: Record<string, string>;
}

export interface SendMessageInput {
  session_id: string;
  user_id: string;
  content: string;
  synthesise_voice?: boolean;
}

export interface InitiateCallInput {
  agent_id: string;
  to_phone_number: string;
  session_id?: string;
}

/** Common pagination parameters accepted by list endpoints. */
export interface PaginationParams {
  limit?: number;
  offset?: number;
}

export interface ListIncidentsParams extends PaginationParams {
  status?: IncidentStatus;
  severity?: Severity;
  feed_id?: UUID;
  assignee_id?: UUID;
}

export interface ListAlertsParams extends PaginationParams {
  status?: AlertStatus;
  severity?: Severity;
  channel?: AlertChannel;
  incident_id?: UUID;
  feed_id?: UUID;
}

export interface ListFeedsParams extends PaginationParams {
  status?: FeedStatus;
  source_type?: FeedSourceType;
  is_enabled?: boolean;
}

export interface ListCallLogsParams extends PaginationParams {
  processing_status?: CallLogProcessingStatus;
  call_id?: UUID;
}

// ---------------------------------------------------------------------------
// Response envelopes
// ---------------------------------------------------------------------------

/**
 * A paginated list response. The backend's `/agents` endpoint returns the
 * collection under an `agents` key; newer collection endpoints are expected to
 * use the generic `items` key. {@link AgentListResponse} models the former.
 */
export interface Paginated<T> {
  items: T[];
  total: number;
  limit: number;
  offset: number;
}

/** Response shape of `GET /agents` (collection key is `agents`). */
export interface AgentListResponse {
  agents: Agent[];
  total: number;
  limit: number;
  offset: number;
}

/** Standard error body returned by the backend: `{ "detail": "..." }`. */
export interface ApiErrorBody {
  detail?: string | { msg: string }[];
  [key: string]: unknown;
}

/** Response shape of `GET /health`. */
export interface HealthResponse {
  status: "ok" | "degraded";
  db: "ok" | "unavailable";
  service: string;
  version: string;
}
