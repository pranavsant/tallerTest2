/**
 * Tests for the injectable HTTP transport (`ApiClient`).
 *
 * These exercise the centralized request building, JSON parsing, and error
 * normalization without any network access — `fetch` is injected as a mock,
 * which is the same seam used to mock the data layer in component tests.
 */

import { ApiClient, ApiError, type FetchLike } from "./http";

/** Build a Response-like object for the mock fetch. */
function jsonResponse(body: unknown, init: { status?: number; ok?: boolean } = {}): Response {
  const status = init.status ?? 200;
  const text = body === undefined ? "" : JSON.stringify(body);
  return {
    ok: init.ok ?? (status >= 200 && status < 300),
    status,
    statusText: "",
    text: () => Promise.resolve(text),
  } as unknown as Response;
}

function mockFetch(impl: (url: string, init?: RequestInit) => Response): {
  fetchFn: FetchLike;
  calls: { url: string; init?: RequestInit }[];
} {
  const calls: { url: string; init?: RequestInit }[] = [];
  const fetchFn: FetchLike = (url, init) => {
    calls.push({ url, init });
    return Promise.resolve(impl(url, init));
  };
  return { fetchFn, calls };
}

describe("ApiClient", () => {
  it("builds the URL from base + path and parses a typed JSON body", async () => {
    const { fetchFn, calls } = mockFetch(() => jsonResponse({ id: "abc", name: "x" }));
    const client = new ApiClient({ baseUrl: "http://api.test", fetchFn });

    const result = await client.get<{ id: string; name: string }>("/incidents/abc");

    expect(result).toEqual({ id: "abc", name: "x" });
    expect(calls[0].url).toBe("http://api.test/incidents/abc");
    expect(calls[0].init?.method).toBe("GET");
  });

  it("strips a trailing slash from the base URL and prefixes the path", async () => {
    const { fetchFn, calls } = mockFetch(() => jsonResponse({}));
    const client = new ApiClient({ baseUrl: "http://api.test/", fetchFn });

    await client.get("agents"); // no leading slash

    expect(calls[0].url).toBe("http://api.test/agents");
  });

  it("serializes query params and omits null/undefined", async () => {
    const { fetchFn, calls } = mockFetch(() => jsonResponse({ items: [] }));
    const client = new ApiClient({ baseUrl: "http://api.test", fetchFn });

    await client.get("/incidents", {
      query: { status: "open", limit: 10, feed_id: undefined, assignee_id: null },
    });

    expect(calls[0].url).toBe("http://api.test/incidents?status=open&limit=10");
  });

  it("sends a JSON body with the right content-type on POST", async () => {
    const { fetchFn, calls } = mockFetch(() => jsonResponse({ ok: true }, { status: 201 }));
    const client = new ApiClient({ baseUrl: "http://api.test", fetchFn });

    await client.post("/agents", { name: "Watcher" });

    const init = calls[0].init!;
    expect(init.method).toBe("POST");
    expect(init.body).toBe(JSON.stringify({ name: "Watcher" }));
    expect((init.headers as Record<string, string>)["Content-Type"]).toBe("application/json");
  });

  it("returns undefined for a 204 No Content response", async () => {
    const { fetchFn } = mockFetch(() => jsonResponse(undefined, { status: 204 }));
    const client = new ApiClient({ baseUrl: "http://api.test", fetchFn });

    const result = await client.delete<void>("/incidents/abc");

    expect(result).toBeUndefined();
  });

  it("throws an ApiError with status and detail message on a non-2xx response", async () => {
    const { fetchFn } = mockFetch(() =>
      jsonResponse({ detail: "Incident not found" }, { status: 404 }),
    );
    const client = new ApiClient({ baseUrl: "http://api.test", fetchFn });

    await expect(client.get("/incidents/missing")).rejects.toMatchObject({
      name: "ApiError",
      status: 404,
      message: "Incident not found",
    });
    await expect(client.get("/incidents/missing")).rejects.toBeInstanceOf(ApiError);
  });

  it("flattens FastAPI validation error arrays into one message", async () => {
    const { fetchFn } = mockFetch(() =>
      jsonResponse(
        { detail: [{ msg: "field required" }, { msg: "must be > 0" }] },
        { status: 422 },
      ),
    );
    const client = new ApiClient({ baseUrl: "http://api.test", fetchFn });

    await expect(client.post("/agents", {})).rejects.toMatchObject({
      status: 422,
      message: "field required; must be > 0",
    });
  });

  it("normalizes a thrown network failure into a network ApiError", async () => {
    const fetchFn: FetchLike = () => Promise.reject(new TypeError("Failed to fetch"));
    const client = new ApiClient({ baseUrl: "http://api.test", fetchFn });

    const err = await client.get("/agents").catch((e: unknown) => e);
    expect(err).toBeInstanceOf(ApiError);
    expect((err as ApiError).isNetworkError).toBe(true);
    expect((err as ApiError).status).toBe(0);
  });

  it("adds an Authorization header when a token provider is configured", async () => {
    const { fetchFn, calls } = mockFetch(() => jsonResponse({}));
    const client = new ApiClient({
      baseUrl: "http://api.test",
      fetchFn,
      getAuthToken: () => "secret-token",
    });

    await client.get("/agents");

    expect((calls[0].init?.headers as Record<string, string>)["Authorization"]).toBe(
      "Bearer secret-token",
    );
  });
});
