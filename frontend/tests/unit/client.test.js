// API client: bearer token, JSON bodies and the spec §10.1 error envelope.
import { describe, expect, it, vi } from "vitest";
import { ApiError, createClient } from "../../src/api/client.js";

function fakeFetch(status, body) {
  return vi.fn(async () => ({
    ok: status >= 200 && status < 300,
    status,
    json: async () => body,
    text: async () => JSON.stringify(body),
  }));
}

describe("createClient", () => {
  it("sends the bearer token and JSON body", async () => {
    const fetchImpl = fakeFetch(200, { ok: true });
    const client = createClient({ fetchImpl, getToken: () => "tok" });
    await client.post("/api/v1/me/goals", { name: "Home" });
    const [url, options] = fetchImpl.mock.calls[0];
    expect(url).toBe("/api/v1/me/goals");
    expect(options.headers.Authorization).toBe("Bearer tok");
    expect(JSON.parse(options.body)).toEqual({ name: "Home" });
  });

  it("raises ApiError with the envelope code", async () => {
    const fetchImpl = fakeFetch(409, { error: { code: "GOAL_REQUIRED", message: "create a goal", details: {} } });
    const client = createClient({ fetchImpl, getToken: () => null });
    await expect(client.post("/api/v1/me/recommendations", {})).rejects.toMatchObject({
      status: 409,
      code: "GOAL_REQUIRED",
      message: "create a goal",
    });
  });

  it("calls onUnauthorized for 401 responses", async () => {
    const onUnauthorized = vi.fn();
    const fetchImpl = fakeFetch(401, { error: { code: "UNAUTHENTICATED", message: "login" } });
    const client = createClient({ fetchImpl, getToken: () => "old", onUnauthorized });
    await expect(client.get("/api/v1/auth/me")).rejects.toBeInstanceOf(ApiError);
    expect(onUnauthorized).toHaveBeenCalledOnce();
  });

  it("returns null for 204 responses", async () => {
    const client = createClient({ fetchImpl: fakeFetch(204, null), getToken: () => "t" });
    expect(await client.post("/api/v1/auth/logout")).toBeNull();
  });
});
