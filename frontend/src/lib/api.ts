/**
 * Typed API client for the Overseer AI FastAPI backend.
 *
 * This module exposes one resource client per backend resource. Each is a thin,
 * fully-typed wrapper over an injectable {@link ApiClient} (see `http.ts`):
 * every method declares its request and response shapes, and all error handling
 * and JSON parsing is centralized in the underlying client.
 *
 * Injectability / mockability
 * ----------------------------
 * Resource clients are produced by factory functions (`createAgentsApi(client)`,
 * …) that take an {@link ApiClient}. In application code you import the default
 * singletons (`agentsApi`, `incidentsApi`, …), which are wired to the
 * `NEXT_PUBLIC_API_BASE_URL` env var. In tests, construct an {@link ApiClient}
 * with a mock `fetch` (or hand a stub object to the factory) and assert against
 * the typed calls.
 *
 * Live vs. planned endpoints
 * --------------------------
 * `agents`, `sessions`, `messages`, and `calls` map to endpoints that exist in
 * the backend today. `incidents`, `alerts`, `feeds`, and `callLogs` follow the
 * same REST conventions and are typed ahead of their controllers landing, so UI
 * work can proceed against a stable contract. They return the generic
 * {@link Paginated} envelope (`items`/`total`/`limit`/`offset`).
 */

import { ApiClient } from "./http";
import { getBrowserAccessToken } from "./supabase/access-token";
import { NEXT_PUBLIC_API_BASE_URL } from "@/env";
import type {
  AdminUser,
  AdminUserListResponse,
  Agent,
  AgentListResponse,
  Alert,
  AssignRoleInput,
  Call,
  CallLog,
  CreateAgentInput,
  Feed,
  HealthResponse,
  Incident,
  InitiateCallInput,
  ListAdminUsersParams,
  ListAgentsParams,
  ListAlertsParams,
  ListCallLogsParams,
  ListFeedsParams,
  ListIncidentsParams,
  Message,
  Paginated,
  SendMessageInput,
  Session,
  SetUserActiveInput,
  StartSessionInput,
  UserRole,
  UUID,
} from "./types";

// Re-export the shared types so consumers can import everything from "@/lib/api".
export * from "./types";
export { ApiClient, ApiError } from "./http";
export type { ApiClientOptions, RequestOptions } from "./http";

// ---------------------------------------------------------------------------
// Default client
// ---------------------------------------------------------------------------

/**
 * The default {@link ApiClient} singleton, pointed at the configured backend.
 * Prefer the per-resource singletons below in components; reach for this when
 * you need a one-off typed request to an endpoint without a resource client.
 */
export const apiClient = new ApiClient({
  baseUrl: NEXT_PUBLIC_API_BASE_URL,
  // In the browser, attach the current Supabase access token so the backend
  // can authenticate the request and enforce the caller's roles. On the server
  // this resolves to null (see `getBrowserAccessToken`), leaving the request
  // unauthenticated — server-side callers should pass their own token.
  getAuthToken: getBrowserAccessToken,
});

// ---------------------------------------------------------------------------
// Agents — /agents (live)
// ---------------------------------------------------------------------------

export function createAgentsApi(client: ApiClient) {
  return {
    /** `GET /agents` — list agents, optionally filtered by status. */
    list(params: ListAgentsParams = {}): Promise<AgentListResponse> {
      return client.get<AgentListResponse>("/agents", {
        query: { status: params.status, limit: params.limit, offset: params.offset },
      });
    },
    /** `GET /agents/{id}` — fetch a single agent. */
    get(agentId: UUID): Promise<Agent> {
      return client.get<Agent>(`/agents/${agentId}`);
    },
    /** `POST /agents` — create a new agent. */
    create(input: CreateAgentInput): Promise<Agent> {
      return client.post<Agent>("/agents", input);
    },
  };
}

// ---------------------------------------------------------------------------
// Sessions — /sessions (live)
// ---------------------------------------------------------------------------

export function createSessionsApi(client: ApiClient) {
  return {
    /** `POST /sessions` — start a new session between a user and an agent. */
    start(input: StartSessionInput): Promise<Session> {
      return client.post<Session>("/sessions", input);
    },
    /** `DELETE /sessions/{id}?user_id=...` — end an active session. */
    end(sessionId: UUID, userId: string): Promise<Session> {
      return client.delete<Session>(`/sessions/${sessionId}`, {
        query: { user_id: userId },
      });
    },
  };
}

// ---------------------------------------------------------------------------
// Messages — /messages (live)
// ---------------------------------------------------------------------------

export function createMessagesApi(client: ApiClient) {
  return {
    /** `POST /messages` — send a message in a session and get the agent reply. */
    send(input: SendMessageInput): Promise<Message> {
      return client.post<Message>("/messages", input);
    },
  };
}

// ---------------------------------------------------------------------------
// Calls — /calls (live)
// ---------------------------------------------------------------------------

export function createCallsApi(client: ApiClient) {
  return {
    /** `POST /calls` — initiate an outbound call via Twilio. */
    initiate(input: InitiateCallInput): Promise<Call> {
      return client.post<Call>("/calls", input);
    },
  };
}

// ---------------------------------------------------------------------------
// Incidents — /incidents (planned)
// ---------------------------------------------------------------------------

export function createIncidentsApi(client: ApiClient) {
  return {
    list(params: ListIncidentsParams = {}): Promise<Paginated<Incident>> {
      return client.get<Paginated<Incident>>("/incidents", { query: { ...params } });
    },
    get(incidentId: UUID): Promise<Incident> {
      return client.get<Incident>(`/incidents/${incidentId}`);
    },
    create(input: Partial<Incident> & Pick<Incident, "title">): Promise<Incident> {
      return client.post<Incident>("/incidents", input);
    },
    update(incidentId: UUID, input: Partial<Incident>): Promise<Incident> {
      return client.patch<Incident>(`/incidents/${incidentId}`, input);
    },
    remove(incidentId: UUID): Promise<void> {
      return client.delete<void>(`/incidents/${incidentId}`);
    },
  };
}

// ---------------------------------------------------------------------------
// Alerts — /alerts (planned)
// ---------------------------------------------------------------------------

export function createAlertsApi(client: ApiClient) {
  return {
    list(params: ListAlertsParams = {}): Promise<Paginated<Alert>> {
      return client.get<Paginated<Alert>>("/alerts", { query: { ...params } });
    },
    get(alertId: UUID): Promise<Alert> {
      return client.get<Alert>(`/alerts/${alertId}`);
    },
    create(input: Partial<Alert> & Pick<Alert, "title">): Promise<Alert> {
      return client.post<Alert>("/alerts", input);
    },
    /** Mark an alert as acknowledged. */
    acknowledge(alertId: UUID): Promise<Alert> {
      return client.post<Alert>(`/alerts/${alertId}/acknowledge`);
    },
    remove(alertId: UUID): Promise<void> {
      return client.delete<void>(`/alerts/${alertId}`);
    },
  };
}

// ---------------------------------------------------------------------------
// Feeds — /feeds (planned)
// ---------------------------------------------------------------------------

export function createFeedsApi(client: ApiClient) {
  return {
    list(params: ListFeedsParams = {}): Promise<Paginated<Feed>> {
      return client.get<Paginated<Feed>>("/feeds", { query: { ...params } });
    },
    get(feedId: UUID): Promise<Feed> {
      return client.get<Feed>(`/feeds/${feedId}`);
    },
    create(input: Partial<Feed> & Pick<Feed, "name" | "source_type">): Promise<Feed> {
      return client.post<Feed>("/feeds", input);
    },
    update(feedId: UUID, input: Partial<Feed>): Promise<Feed> {
      return client.patch<Feed>(`/feeds/${feedId}`, input);
    },
    remove(feedId: UUID): Promise<void> {
      return client.delete<void>(`/feeds/${feedId}`);
    },
  };
}

// ---------------------------------------------------------------------------
// Call logs — /call-logs (planned)
// ---------------------------------------------------------------------------

export function createCallLogsApi(client: ApiClient) {
  return {
    list(params: ListCallLogsParams = {}): Promise<Paginated<CallLog>> {
      return client.get<Paginated<CallLog>>("/call-logs", { query: { ...params } });
    },
    get(callLogId: UUID): Promise<CallLog> {
      return client.get<CallLog>(`/call-logs/${callLogId}`);
    },
  };
}

// ---------------------------------------------------------------------------
// Admin — /admin (live) — user & role management; admin-only on the backend
// ---------------------------------------------------------------------------

export function createAdminApi(client: ApiClient) {
  return {
    /** `GET /admin/users` — list users and their assigned roles. */
    listUsers(params: ListAdminUsersParams = {}): Promise<AdminUserListResponse> {
      return client.get<AdminUserListResponse>("/admin/users", {
        query: { page: params.page, per_page: params.per_page },
      });
    },
    /** `PUT /admin/users/{id}/role` — assign a role to a user. */
    assignRole(userId: UUID, input: AssignRoleInput): Promise<AdminUser> {
      return client.put<AdminUser>(`/admin/users/${userId}/role`, input);
    },
    /** `PUT /admin/users/{id}/status` — deactivate or reactivate an account. */
    setActive(userId: UUID, input: SetUserActiveInput): Promise<AdminUser> {
      return client.put<AdminUser>(`/admin/users/${userId}/status`, input);
    },
  };
}

// ---------------------------------------------------------------------------
// Health — /health (live)
// ---------------------------------------------------------------------------

export function createHealthApi(client: ApiClient) {
  return {
    check(): Promise<HealthResponse> {
      return client.get<HealthResponse>("/health");
    },
  };
}

// ---------------------------------------------------------------------------
// Default resource-client singletons (wired to the default apiClient)
// ---------------------------------------------------------------------------

export const agentsApi = createAgentsApi(apiClient);
export const sessionsApi = createSessionsApi(apiClient);
export const messagesApi = createMessagesApi(apiClient);
export const callsApi = createCallsApi(apiClient);
export const incidentsApi = createIncidentsApi(apiClient);
export const alertsApi = createAlertsApi(apiClient);
export const feedsApi = createFeedsApi(apiClient);
export const callLogsApi = createCallLogsApi(apiClient);
export const adminApi = createAdminApi(apiClient);
export const healthApi = createHealthApi(apiClient);

/** Convenience type for any resource client (handy for DI in components). */
export type AgentsApi = ReturnType<typeof createAgentsApi>;
export type SessionsApi = ReturnType<typeof createSessionsApi>;
export type MessagesApi = ReturnType<typeof createMessagesApi>;
export type CallsApi = ReturnType<typeof createCallsApi>;
export type IncidentsApi = ReturnType<typeof createIncidentsApi>;
export type AlertsApi = ReturnType<typeof createAlertsApi>;
export type FeedsApi = ReturnType<typeof createFeedsApi>;
export type CallLogsApi = ReturnType<typeof createCallLogsApi>;
export type AdminApi = ReturnType<typeof createAdminApi>;
export type HealthApi = ReturnType<typeof createHealthApi>;
