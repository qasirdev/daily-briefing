import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { fetchBriefing, getApiBase } from "@/lib/api";

describe("getApiBase", () => {
  const originalEnv = process.env.NEXT_PUBLIC_API_BASE_URL;

  beforeEach(() => {
    delete process.env.NEXT_PUBLIC_API_BASE_URL;
  });

  afterEach(() => {
    if (originalEnv === undefined) {
      delete process.env.NEXT_PUBLIC_API_BASE_URL;
    } else {
      process.env.NEXT_PUBLIC_API_BASE_URL = originalEnv;
    }
    vi.unstubAllGlobals();
  });

  it("prefers NEXT_PUBLIC_API_BASE_URL when set", () => {
    process.env.NEXT_PUBLIC_API_BASE_URL = "https://api.example.com/";
    expect(getApiBase()).toBe("https://api.example.com");
  });

  it("uses same origin on Docker/nginx UI ports", () => {
    vi.stubGlobal("window", {
      location: { port: "8088", origin: "http://localhost:8088", hostname: "localhost" },
    } as Window & typeof globalThis);
    expect(getApiBase()).toBe("http://localhost:8088");
  });

  it("uses same origin for localhost without explicit port", () => {
    vi.stubGlobal("window", {
      location: { port: "", origin: "http://localhost", hostname: "localhost" },
    } as Window & typeof globalThis);
    expect(getApiBase()).toBe("http://localhost");
  });

  it("falls back to local uvicorn when no override matches", () => {
    vi.stubGlobal("window", {
      location: { port: "3010", origin: "http://localhost:3010", hostname: "localhost" },
    } as Window & typeof globalThis);
    expect(getApiBase()).toBe("http://127.0.0.1:8010");
  });
});

describe("fetchBriefing", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("parses a successful briefing response", async () => {
    const responseBody = {
      status: "success",
      briefing: "<p>Hello</p>",
      metadata: {
        trace_id: "a".repeat(32),
        total_tokens: 10,
        total_cost_usd: 0,
        execution_ms: 100,
        model_used: "openai/gpt-4o-mini",
        agents_invoked: ["focus"],
        agent_breakdown: [],
      },
    };

    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => responseBody,
      }),
    );

    const parsed = await fetchBriefing("user-1");
    expect(parsed.status).toBe("success");
    expect(parsed.briefing).toBe("<p>Hello</p>");
  });

  it("throws when the API returns a non-OK status", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: false,
        status: 429,
        json: async () => ({ detail: "Rate limit exceeded" }),
      }),
    );

    await expect(fetchBriefing("user-1")).rejects.toThrow("Rate limit exceeded");
  });

  it("rejects malformed success payloads", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => ({ status: "success" }),
      }),
    );

    await expect(fetchBriefing("user-1")).rejects.toThrow();
  });
});
