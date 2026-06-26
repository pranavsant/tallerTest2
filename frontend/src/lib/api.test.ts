/**
 * Tests for the resource clients — verifying they are injectable/mockable and
 * map to the correct HTTP method + path for each backend operation.
 */

import { ApiClient, type FetchLike } from "./http";
import {
  createAdminApi,
  createAgentsApi,
  createIncidentsApi,
  createSessionsApi,
} from "./api";

function recorder(): {
  fetchFn: FetchLike;
  calls: { url: string; method?: string; body?: string }[];
} {
  const calls: { url: string; method?: string; body?: string }[] = [];
  const fetchFn: FetchLike = (url, init) => {
    calls.push({
      url,
      method: init?.method,
      body: init?.body as string | undefined,
    });
    return Promise.resolve({
      ok: true,
      status: 200,
      statusText: "",
      text: () => Promise.resolve(JSON.stringify({ agents: [], total: 0 })),
    } as unknown as Response);
  };
  return { fetchFn, calls };
}

describe("resource clients", () => {
  it("agentsApi.list issues GET /agents with query params", async () => {
    const { fetchFn, calls } = recorder();
    const agents = createAgentsApi(new ApiClient({ baseUrl: "http://api.test", fetchFn }));

    await agents.list({ status: "active", limit: 25 });

    expect(calls[0].method).toBe("GET");
    expect(calls[0].url).toBe("http://api.test/agents?status=active&limit=25");
  });

  it("agentsApi.create issues POST /agents with a JSON body", async () => {
    const { fetchFn, calls } = recorder();
    const agents = createAgentsApi(new ApiClient({ baseUrl: "http://api.test", fetchFn }));

    await agents.create({ name: "W", system_prompt: "p", voice_id: "v" });

    expect(calls[0].method).toBe("POST");
    expect(calls[0].url).toBe("http://api.test/agents");
    expect(calls[0].body).toBe(JSON.stringify({ name: "W", system_prompt: "p", voice_id: "v" }));
  });

  it("sessionsApi.end issues DELETE with the user_id query param", async () => {
    const { fetchFn, calls } = recorder();
    const sessions = createSessionsApi(new ApiClient({ baseUrl: "http://api.test", fetchFn }));

    await sessions.end("sess-1", "user-1");

    expect(calls[0].method).toBe("DELETE");
    expect(calls[0].url).toBe("http://api.test/sessions/sess-1?user_id=user-1");
  });

  it("incidentsApi.list issues GET /incidents and is fully mockable", async () => {
    const { fetchFn, calls } = recorder();
    const incidents = createIncidentsApi(new ApiClient({ baseUrl: "http://api.test", fetchFn }));

    await incidents.list({ severity: "high", status: "open" });

    expect(calls[0].method).toBe("GET");
    expect(calls[0].url).toBe("http://api.test/incidents?severity=high&status=open");
  });

  it("adminApi.listUsers issues GET /admin/users with pagination", async () => {
    const { fetchFn, calls } = recorder();
    const admin = createAdminApi(new ApiClient({ baseUrl: "http://api.test", fetchFn }));

    await admin.listUsers({ page: 2, per_page: 25 });

    expect(calls[0].method).toBe("GET");
    expect(calls[0].url).toBe("http://api.test/admin/users?page=2&per_page=25");
  });

  it("adminApi.assignRole issues PUT /admin/users/{id}/role with the role body", async () => {
    const { fetchFn, calls } = recorder();
    const admin = createAdminApi(new ApiClient({ baseUrl: "http://api.test", fetchFn }));

    await admin.assignRole("user-1", { role: "operator" });

    expect(calls[0].method).toBe("PUT");
    expect(calls[0].url).toBe("http://api.test/admin/users/user-1/role");
    expect(calls[0].body).toBe(JSON.stringify({ role: "operator" }));
  });

  it("a resource client can be driven by a hand-written stub (no ApiClient)", async () => {
    // The factory only needs an object with the verb methods it calls — so a
    // plain stub stands in for ApiClient in unit tests of higher-level code.
    const stub = {
      get: jest.fn().mockResolvedValue({ agents: [], total: 0, limit: 50, offset: 0 }),
    } as unknown as ApiClient;
    const agents = createAgentsApi(stub);

    const res = await agents.list();

    expect(res.total).toBe(0);
    expect(stub.get).toHaveBeenCalledWith("/agents", expect.anything());
  });
});
