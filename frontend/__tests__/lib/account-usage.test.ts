import { beforeEach, describe, expect, it, vi } from "vitest";

import {
  fetchAccountUsage,
  formatAccountUsageSummary,
  type AccountUsage,
} from "@/lib/account-usage";

describe("account-usage", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("formats unavailable usage with message", () => {
    const usage: AccountUsage = {
      available: false,
      source: "unavailable",
      fetched_at: new Date().toISOString(),
      message: "No API key configured",
    };
    expect(formatAccountUsageSummary(usage)).toBe("No API key configured");
  });

  it("formats available usage with spend buckets", () => {
    const usage: AccountUsage = {
      available: true,
      source: "openrouter_key",
      fetched_at: new Date().toISOString(),
      usage_all_time_usd: 1.234,
      usage_monthly_usd: 0.005,
      usage_daily_usd: 0.0004,
    };
    expect(formatAccountUsageSummary(usage)).toContain("all-time $1.23");
    expect(formatAccountUsageSummary(usage)).toContain("this month $0.0050");
    expect(formatAccountUsageSummary(usage)).toContain("today $0.0004");
  });

  it("returns generic copy when available without amounts", () => {
    const usage: AccountUsage = {
      available: true,
      source: "openrouter_key",
      fetched_at: new Date().toISOString(),
    };
    expect(formatAccountUsageSummary(usage)).toBe("OpenRouter account usage available");
  });

  it("returns null when fetch fails", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: false,
        json: async () => ({}),
      }),
    );
    await expect(fetchAccountUsage()).resolves.toBeNull();
  });

  it("parses successful account usage response", async () => {
    const payload = {
      available: true,
      source: "openrouter_key",
      fetched_at: new Date().toISOString(),
      usage_all_time_usd: 0.5,
    };
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => payload,
      }),
    );
    await expect(fetchAccountUsage()).resolves.toMatchObject({
      available: true,
      usage_all_time_usd: 0.5,
    });
  });
});
