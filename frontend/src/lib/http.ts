/**
 * Typed HTTP client for the FastAPI backend.
 *
 * Responsibilities (all centralized here, never in callers):
 *  - Building request URLs (base URL + path + query string).
 *  - Serializing JSON request bodies and setting headers.
 *  - Parsing JSON responses into typed shapes.
 *  - Normalizing every non-2xx response into a single {@link ApiError}.
 *  - Normalizing network/parse failures into {@link ApiError} as well.
 *
 * The client is intentionally framework-agnostic and injectable: it takes its
 * `fetch` implementation and base URL via options, so it can be constructed
 * with a mock `fetch` in tests (see `apiClient.test.ts`). The resource clients
 * in `api.ts` accept an {@link ApiClient} instance, which makes the whole data
 * layer mockable without touching global state.
 */

import type { ApiErrorBody } from "./types";

/** A `fetch`-compatible function. Defaults to the global `fetch`. */
export type FetchLike = (input: string, init?: RequestInit) => Promise<Response>;

/** Query parameters. `undefined`/`null` values are omitted from the URL. */
export type QueryParams = Record<string, string | number | boolean | null | undefined>;

export interface ApiClientOptions {
  /** Base URL of the API, e.g. "http://localhost:8000". No trailing slash required. */
  baseUrl: string;
  /** Injected fetch implementation. Defaults to the global `fetch`. */
  fetchFn?: FetchLike;
  /** Default headers merged into every request. */
  defaultHeaders?: Record<string, string>;
  /**
   * Optional async hook returning an auth token. When provided and it resolves
   * to a non-empty value, an `Authorization: Bearer <token>` header is added.
   */
  getAuthToken?: () => string | null | undefined | Promise<string | null | undefined>;
  /** Optional per-request timeout in milliseconds. Omit for no timeout. */
  timeoutMs?: number;
}

export interface RequestOptions {
  /** Query string parameters. */
  query?: QueryParams;
  /** Extra headers for this request. */
  headers?: Record<string, string>;
  /** Per-request `AbortSignal`. Composed with the configured timeout. */
  signal?: AbortSignal;
}

/**
 * The single error type thrown by every {@link ApiClient} method. Carries the
 * HTTP status, the parsed response body (when available), and a human-readable
 * message extracted from the backend's `{ "detail": ... }` envelope.
 */
export class ApiError extends Error {
  readonly status: number;
  readonly body: ApiErrorBody | null;
  /** Set when the failure was a network/timeout error rather than an HTTP status. */
  readonly isNetworkError: boolean;

  constructor(
    message: string,
    status: number,
    body: ApiErrorBody | null = null,
    isNetworkError = false,
  ) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.body = body;
    this.isNetworkError = isNetworkError;
    // Restore prototype chain for instanceof across transpilation targets.
    Object.setPrototypeOf(this, ApiError.prototype);
  }
}

/** Extract a human-readable message from a parsed error body. */
function messageFromBody(body: ApiErrorBody | null, fallback: string): string {
  if (!body) return fallback;
  const { detail } = body;
  if (typeof detail === "string" && detail.length > 0) return detail;
  // FastAPI validation errors: detail is an array of { msg, loc, ... }.
  if (Array.isArray(detail) && detail.length > 0) {
    const msgs = detail
      .map((d) => (d && typeof d.msg === "string" ? d.msg : null))
      .filter((m): m is string => Boolean(m));
    if (msgs.length > 0) return msgs.join("; ");
  }
  return fallback;
}

function buildQueryString(query?: QueryParams): string {
  if (!query) return "";
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(query)) {
    if (value === undefined || value === null) continue;
    params.append(key, String(value));
  }
  const qs = params.toString();
  return qs ? `?${qs}` : "";
}

export class ApiClient {
  private readonly baseUrl: string;
  private readonly injectedFetch?: FetchLike;
  private readonly defaultHeaders: Record<string, string>;
  private readonly getAuthToken?: ApiClientOptions["getAuthToken"];
  private readonly timeoutMs?: number;

  constructor(options: ApiClientOptions) {
    this.baseUrl = options.baseUrl.replace(/\/+$/, "");
    this.injectedFetch = options.fetchFn;
    this.defaultHeaders = options.defaultHeaders ?? {};
    this.getAuthToken = options.getAuthToken;
    this.timeoutMs = options.timeoutMs;
  }

  /**
   * Resolve the fetch implementation lazily (at request time, not construction
   * time) so that constructing a client never requires a global `fetch` to be
   * present — important for SSR/module-load and for test environments without
   * a global fetch. An injected `fetchFn` always takes precedence.
   */
  private resolveFetch(): FetchLike {
    if (this.injectedFetch) return this.injectedFetch;
    if (typeof fetch !== "undefined") return fetch.bind(globalThis) as FetchLike;
    throw new ApiError(
      "No fetch implementation available. Pass `fetchFn` to ApiClient.",
      0,
      null,
      true,
    );
  }

  // ── Verb helpers ──────────────────────────────────────────────────────────

  get<T>(path: string, options?: RequestOptions): Promise<T> {
    return this.request<T>("GET", path, undefined, options);
  }

  post<T>(path: string, body?: unknown, options?: RequestOptions): Promise<T> {
    return this.request<T>("POST", path, body, options);
  }

  put<T>(path: string, body?: unknown, options?: RequestOptions): Promise<T> {
    return this.request<T>("PUT", path, body, options);
  }

  patch<T>(path: string, body?: unknown, options?: RequestOptions): Promise<T> {
    return this.request<T>("PATCH", path, body, options);
  }

  delete<T>(path: string, options?: RequestOptions): Promise<T> {
    return this.request<T>("DELETE", path, undefined, options);
  }

  // ── Core request ────────────────────────────────────────────────────────

  /**
   * Issue a request and return the parsed JSON body typed as `T`.
   *
   * - 2xx with a JSON body → parsed body as `T`.
   * - 2xx with an empty body (e.g. 204) → `undefined as T`.
   * - non-2xx → throws {@link ApiError} with status + parsed body.
   * - network/timeout/parse failure → throws {@link ApiError} (`isNetworkError`).
   */
  async request<T>(
    method: string,
    path: string,
    body?: unknown,
    options: RequestOptions = {},
  ): Promise<T> {
    const url = `${this.baseUrl}${path.startsWith("/") ? path : `/${path}`}${buildQueryString(
      options.query,
    )}`;

    const headers: Record<string, string> = {
      Accept: "application/json",
      ...this.defaultHeaders,
      ...options.headers,
    };

    const init: RequestInit = { method, headers };

    if (body !== undefined) {
      headers["Content-Type"] = "application/json";
      init.body = JSON.stringify(body);
    }

    if (this.getAuthToken) {
      const token = await this.getAuthToken();
      if (token) headers["Authorization"] = `Bearer ${token}`;
    }

    // Compose the caller's signal with an optional timeout.
    const { signal, cleanup } = this.buildSignal(options.signal);
    if (signal) init.signal = signal;

    const fetchFn = this.resolveFetch();
    let response: Response;
    try {
      response = await fetchFn(url, init);
    } catch (err) {
      cleanup();
      if (err instanceof DOMException && err.name === "AbortError") {
        throw new ApiError("Request aborted or timed out", 0, null, true);
      }
      const detail = err instanceof Error ? err.message : "Network request failed";
      throw new ApiError(detail, 0, null, true);
    }
    cleanup();

    return this.parseResponse<T>(response);
  }

  private async parseResponse<T>(response: Response): Promise<T> {
    // 204 No Content (and 205) carry no body.
    if (response.status === 204 || response.status === 205) {
      if (!response.ok) {
        throw new ApiError(response.statusText || "Request failed", response.status);
      }
      return undefined as T;
    }

    const text = await response.text();
    let parsed: unknown = undefined;
    if (text.length > 0) {
      try {
        parsed = JSON.parse(text);
      } catch {
        if (!response.ok) {
          throw new ApiError(text || response.statusText || "Request failed", response.status);
        }
        throw new ApiError("Failed to parse response body as JSON", response.status, null, true);
      }
    }

    if (!response.ok) {
      const errorBody = (parsed ?? null) as ApiErrorBody | null;
      const message = messageFromBody(
        errorBody,
        response.statusText || `Request failed with status ${response.status}`,
      );
      throw new ApiError(message, response.status, errorBody);
    }

    return parsed as T;
  }

  /** Build a combined abort signal from the caller's signal + configured timeout. */
  private buildSignal(callerSignal?: AbortSignal): {
    signal?: AbortSignal;
    cleanup: () => void;
  } {
    if (!this.timeoutMs && !callerSignal) return { cleanup: () => {} };

    const controller = new AbortController();
    const timers: ReturnType<typeof setTimeout>[] = [];

    if (callerSignal) {
      if (callerSignal.aborted) controller.abort();
      else callerSignal.addEventListener("abort", () => controller.abort(), { once: true });
    }

    if (this.timeoutMs) {
      timers.push(setTimeout(() => controller.abort(), this.timeoutMs));
    }

    return {
      signal: controller.signal,
      cleanup: () => timers.forEach(clearTimeout),
    };
  }
}
