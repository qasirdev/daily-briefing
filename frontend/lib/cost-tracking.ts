const STORAGE_KEY = "daily-briefing:usage-tracking";

export type UsageTracking = {
  cumulativeCostUsd: number;
  cumulativeRuns: number;
  cumulativeTokens: number;
};

export type VisitUsageStats = {
  runsSinceLastVisit: number;
  costSinceLastVisit: number;
  tokensSinceLastVisit: number;
  visitAvgCostPerRun: number;
  lifetimeRuns: number;
  lifetimeCostUsd: number;
  lifetimeTokens: number;
  lifetimeAvgCostPerRun: number;
};

const EMPTY_TRACKING: UsageTracking = {
  cumulativeCostUsd: 0,
  cumulativeRuns: 0,
  cumulativeTokens: 0,
};

export function readUsageTracking(): UsageTracking {
  if (typeof window === "undefined") {
    return { ...EMPTY_TRACKING };
  }
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) {
      return { ...EMPTY_TRACKING };
    }
    const parsed: unknown = JSON.parse(raw);
    if (!parsed || typeof parsed !== "object") {
      return { ...EMPTY_TRACKING };
    }
    const record = parsed as Partial<UsageTracking>;
    return {
      cumulativeCostUsd:
        typeof record.cumulativeCostUsd === "number" && record.cumulativeCostUsd >= 0
          ? record.cumulativeCostUsd
          : 0,
      cumulativeRuns:
        typeof record.cumulativeRuns === "number" && record.cumulativeRuns >= 0
          ? record.cumulativeRuns
          : 0,
      cumulativeTokens:
        typeof record.cumulativeTokens === "number" && record.cumulativeTokens >= 0
          ? record.cumulativeTokens
          : 0,
    };
  } catch {
    return { ...EMPTY_TRACKING };
  }
}

export function writeUsageTracking(tracking: UsageTracking): void {
  if (typeof window === "undefined") {
    return;
  }
  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(tracking));
}

export function recordBriefingUsage(costUsd: number, tokens: number): UsageTracking {
  const current = readUsageTracking();
  const next: UsageTracking = {
    cumulativeCostUsd: current.cumulativeCostUsd + costUsd,
    cumulativeRuns: current.cumulativeRuns + 1,
    cumulativeTokens: current.cumulativeTokens + tokens,
  };
  writeUsageTracking(next);
  return next;
}

export function computeVisitStats(baseline: UsageTracking, current: UsageTracking): VisitUsageStats {
  const runsSinceLastVisit = Math.max(current.cumulativeRuns - baseline.cumulativeRuns, 0);
  const costSinceLastVisit = Math.max(current.cumulativeCostUsd - baseline.cumulativeCostUsd, 0);
  const tokensSinceLastVisit = Math.max(current.cumulativeTokens - baseline.cumulativeTokens, 0);
  const visitAvgCostPerRun = runsSinceLastVisit > 0 ? costSinceLastVisit / runsSinceLastVisit : 0;
  const lifetimeAvgCostPerRun =
    current.cumulativeRuns > 0 ? current.cumulativeCostUsd / current.cumulativeRuns : 0;

  return {
    runsSinceLastVisit,
    costSinceLastVisit,
    tokensSinceLastVisit,
    visitAvgCostPerRun,
    lifetimeRuns: current.cumulativeRuns,
    lifetimeCostUsd: current.cumulativeCostUsd,
    lifetimeTokens: current.cumulativeTokens,
    lifetimeAvgCostPerRun,
  };
}
