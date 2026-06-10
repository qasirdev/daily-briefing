"use client";

import { useState } from "react";

import {
  formatCostUsd,
  isOrchestratorSummary,
  type ObservabilityData,
} from "@/lib/briefing-schema";
import { formatAccountUsageSummary, type AccountUsage } from "@/lib/account-usage";
import type { VisitUsageStats } from "@/lib/cost-tracking";

type ObservabilityBadgeProps = {
  data: ObservabilityData;
  visitStats?: VisitUsageStats | null;
  accountUsage?: AccountUsage | null;
};

function truncateModel(model: string, max = 28): string {
  if (model.length <= max) {
    return model;
  }
  return `${model.slice(0, max - 1)}…`;
}

function statusClasses(status: ObservabilityData["status"]): string {
  if (status === "degraded" || status === "awaiting_consent") {
    return "text-amber-700 dark:text-amber-400";
  }
  if (status === "failure") {
    return "text-red-700 dark:text-red-400";
  }
  return "text-emerald-700 dark:text-emerald-400";
}

function formatVisitSummary(stats: VisitUsageStats): string {
  if (stats.runsSinceLastVisit === 0) {
    return "No briefings generated this visit yet.";
  }
  const runLabel = stats.runsSinceLastVisit === 1 ? "run" : "runs";
  const visitAvgHint =
    stats.visitAvgCostPerRun > 0
      ? ` (~${formatCostUsd(stats.visitAvgCostPerRun)}/run)`
      : "";
  return `This visit: ${stats.runsSinceLastVisit} ${runLabel} · ${formatCostUsd(stats.costSinceLastVisit)}${visitAvgHint}`;
}

export function ObservabilityBadge({
  data,
  visitStats = null,
  accountUsage = null,
}: ObservabilityBadgeProps) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="rounded-lg border border-black/10 bg-zinc-50 p-4 text-sm dark:border-white/10 dark:bg-zinc-900">
      <div className="flex flex-wrap items-center gap-4 text-zinc-700 dark:text-zinc-200">
        <span title="Total execution time" aria-label={`Execution time ${data.executionMs} milliseconds`}>
          ⏱ {data.executionMs}ms
        </span>
        <span title="Total tokens used" aria-label={`Tokens used ${data.tokensUsed}`}>
          🧠 {data.tokensUsed} tokens
        </span>
        <span title="Total LLM cost" aria-label={`Total cost ${data.totalCostUsd} dollars`}>
          💰 {formatCostUsd(data.totalCostUsd)}
        </span>
        <span
          title={data.modelUsed}
          aria-label={`Model ${data.modelUsed}`}
          className="max-w-[12rem] truncate"
        >
          🤖 {truncateModel(data.modelUsed)}
        </span>
        <span className={statusClasses(data.status)} title="Pipeline status">
          {data.status === "degraded" ? "⚠ Degraded" : data.status}
        </span>
        <button
          type="button"
          className="ml-auto text-briefing-primary underline-offset-2 hover:underline"
          aria-expanded={expanded}
          aria-controls="agent-breakdown"
          onClick={() => setExpanded((value) => !value)}
        >
          {expanded ? "Hide agents" : "Show agents"}
        </button>
      </div>

      {visitStats || accountUsage ? (
        <div className="mt-2 space-y-1 text-xs text-zinc-500 dark:text-zinc-400">
          {visitStats ? (
            <p>
              {formatVisitSummary(visitStats)}
              {visitStats.lifetimeRuns > 0 ? (
                <span>
                  {" "}
                  · Lifetime (this browser): {visitStats.lifetimeRuns}{" "}
                  {visitStats.lifetimeRuns === 1 ? "run" : "runs"} ·{" "}
                  {formatCostUsd(visitStats.lifetimeCostUsd)}
                  {visitStats.lifetimeAvgCostPerRun > 0
                    ? ` (~${formatCostUsd(visitStats.lifetimeAvgCostPerRun)}/run avg)`
                    : ""}
                </span>
              ) : null}
            </p>
          ) : null}
          {accountUsage ? (
            <p
              title={
                accountUsage.available
                  ? "Cumulative spend for the OpenRouter API key configured on the backend"
                  : accountUsage.message ?? undefined
              }
            >
              OpenRouter account
              {accountUsage.label ? ` (${accountUsage.label})` : ""}:{" "}
              {formatAccountUsageSummary(accountUsage)}
              {accountUsage.limit_remaining_usd != null ? (
                <span> · {formatCostUsd(accountUsage.limit_remaining_usd)} remaining</span>
              ) : null}
            </p>
          ) : null}
        </div>
      ) : null}

      {expanded ? (
        <div className="mt-3 border-t border-black/5 pt-3 dark:border-white/10">
          <ul id="agent-breakdown" className="space-y-2">
            {data.agentBreakdown.length === 0 ? (
              <li className="text-zinc-500">No per-agent metrics available.</li>
            ) : (
              data.agentBreakdown.map((agent) => {
                const orchestratorRow = isOrchestratorSummary(agent);
                return (
                  <li
                    key={agent.agent_id}
                    className={`flex flex-wrap gap-3 ${
                      orchestratorRow
                        ? "text-zinc-500 dark:text-zinc-400"
                        : "text-zinc-600 dark:text-zinc-300"
                    }`}
                  >
                    <span className="font-medium capitalize">{agent.agent_id}</span>
                    <span>{agent.execution_ms}ms</span>
                    {orchestratorRow ? (
                      <span
                        title={`${agent.tokens_used.toLocaleString()} tokens — session total already counted above; orchestrator does not call an LLM`}
                      >
                        session total (not billed)
                      </span>
                    ) : (
                      <span>{agent.tokens_used.toLocaleString()} tokens</span>
                    )}
                    <span>{formatCostUsd(agent.cost_usd ?? 0)}</span>
                    <span>{truncateModel(agent.model_used, 20)}</span>
                    <span>{agent.status}</span>
                  </li>
                );
              })
            )}
          </ul>
          <p className="mt-3 text-xs text-zinc-500 dark:text-zinc-400">
            Per-agent tokens are LLM usage only. Orchestrator shows the pipeline total for
            reference — it is not a second charge. Task and calendar use MCP tools without LLM
            tokens.
          </p>
        </div>
      ) : null}
    </div>
  );
}
