import { beforeEach, describe, expect, it } from "vitest";

import {
  computeVisitStats,
  readUsageTracking,
  recordBriefingUsage,
  writeUsageTracking,
  type UsageTracking,
} from "@/lib/cost-tracking";

const STORAGE_KEY = "daily-briefing:usage-tracking";

describe("cost-tracking", () => {
  beforeEach(() => {
    window.localStorage.clear();
  });

  it("returns empty tracking when storage is missing", () => {
    expect(readUsageTracking()).toEqual({
      cumulativeCostUsd: 0,
      cumulativeRuns: 0,
      cumulativeTokens: 0,
    });
  });

  it("ignores invalid stored payloads", () => {
    window.localStorage.setItem(STORAGE_KEY, "not-json");
    expect(readUsageTracking()).toEqual({
      cumulativeCostUsd: 0,
      cumulativeRuns: 0,
      cumulativeTokens: 0,
    });
  });

  it("normalizes negative numbers to zero", () => {
    writeUsageTracking({
      cumulativeCostUsd: -1,
      cumulativeRuns: -2,
      cumulativeTokens: -3,
    });
    expect(readUsageTracking()).toEqual({
      cumulativeCostUsd: 0,
      cumulativeRuns: 0,
      cumulativeTokens: 0,
    });
  });

  it("records briefing usage and persists totals", () => {
    const next = recordBriefingUsage(0.02, 120);
    expect(next).toEqual({
      cumulativeCostUsd: 0.02,
      cumulativeRuns: 1,
      cumulativeTokens: 120,
    });
    expect(readUsageTracking()).toEqual(next);
  });

  it("computes visit stats with averages", () => {
    const baseline: UsageTracking = {
      cumulativeCostUsd: 0.01,
      cumulativeRuns: 1,
      cumulativeTokens: 50,
    };
    const current: UsageTracking = {
      cumulativeCostUsd: 0.04,
      cumulativeRuns: 3,
      cumulativeTokens: 200,
    };

    expect(computeVisitStats(baseline, current)).toEqual({
      runsSinceLastVisit: 2,
      costSinceLastVisit: 0.03,
      tokensSinceLastVisit: 150,
      visitAvgCostPerRun: 0.015,
      lifetimeRuns: 3,
      lifetimeCostUsd: 0.04,
      lifetimeTokens: 200,
      lifetimeAvgCostPerRun: 0.04 / 3,
    });
  });

  it("handles zero-run visit averages", () => {
    const empty: UsageTracking = {
      cumulativeCostUsd: 0,
      cumulativeRuns: 0,
      cumulativeTokens: 0,
    };
    expect(computeVisitStats(empty, empty).visitAvgCostPerRun).toBe(0);
    expect(computeVisitStats(empty, empty).lifetimeAvgCostPerRun).toBe(0);
  });
});
