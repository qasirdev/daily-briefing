"use client";

import { useState } from "react";

import type { ObservabilityData } from "@/lib/briefing-schema";

type ObservabilityBadgeProps = {
  data: ObservabilityData;
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

export function ObservabilityBadge({ data }: ObservabilityBadgeProps) {
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

      {expanded ? (
        <ul id="agent-breakdown" className="mt-3 space-y-2 border-t border-black/5 pt-3 dark:border-white/10">
          {data.agentBreakdown.length === 0 ? (
            <li className="text-zinc-500">No per-agent metrics available.</li>
          ) : (
            data.agentBreakdown.map((agent) => (
              <li key={agent.agent_id} className="flex flex-wrap gap-3 text-zinc-600 dark:text-zinc-300">
                <span className="font-medium capitalize">{agent.agent_id}</span>
                <span>{agent.execution_ms}ms</span>
                <span>{agent.tokens_used} tokens</span>
                <span>{truncateModel(agent.model_used, 20)}</span>
                <span>{agent.status}</span>
              </li>
            ))
          )}
        </ul>
      ) : null}
    </div>
  );
}
