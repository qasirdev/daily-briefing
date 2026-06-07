"use client";

import { useState } from "react";

import { ReasoningFeedback } from "@/components/ReasoningFeedback";
import type { ReasoningTrace as ReasoningTraceData } from "@/lib/briefing-schema";

type ReasoningTraceProps = {
  trace: ReasoningTraceData | null | undefined;
  briefingId?: string;
};

function layerLabel(layer: string): string {
  return layer.replace(/_/g, " ");
}

export function ReasoningTrace({ trace, briefingId }: ReasoningTraceProps) {
  const [expanded, setExpanded] = useState(false);

  if (!trace || trace.entries.length === 0) {
    return null;
  }

  return (
    <div className="rounded-lg border border-black/10 bg-white p-4 dark:border-white/10 dark:bg-zinc-950">
      <div className="flex flex-wrap items-center gap-3">
        <h3 className="text-sm font-semibold text-foreground">Agent reasoning trace</h3>
        <span className="rounded-full bg-zinc-100 px-2 py-0.5 text-xs text-zinc-600 dark:bg-zinc-800 dark:text-zinc-300">
          {trace.hitl_mode === "human_on_the_loop" ? "Human-on-the-loop" : "Human-in-the-loop"}
        </span>
        <button
          type="button"
          className="ml-auto text-sm text-briefing-primary underline-offset-2 hover:underline"
          aria-expanded={expanded}
          aria-controls="reasoning-trace-list"
          onClick={() => setExpanded((value) => !value)}
        >
          {expanded ? "Hide trace" : `Show ${trace.entries.length} steps`}
        </button>
      </div>

      {expanded ? (
        <ol id="reasoning-trace-list" className="mt-4 space-y-3 border-t border-black/5 pt-4 dark:border-white/10">
          {trace.entries.map((entry, index) => (
            <li key={`${entry.agent_id}-${index}`} className="text-sm">
              <div className="flex flex-wrap items-center gap-2 text-zinc-800 dark:text-zinc-100">
                <span className="font-medium capitalize">{entry.agent_id}</span>
                <span className="rounded bg-zinc-100 px-1.5 py-0.5 text-xs uppercase tracking-wide text-zinc-600 dark:bg-zinc-800 dark:text-zinc-300">
                  {layerLabel(entry.hitl_layer)}
                </span>
                <span className="text-xs text-zinc-500">{entry.status}</span>
              </div>
              <p className="mt-1 text-zinc-600 dark:text-zinc-300">{entry.summary}</p>
              {entry.execution_ms > 0 ? (
                <p className="mt-1 text-xs text-zinc-500">
                  {entry.execution_ms}ms · {entry.tokens_used} tokens
                </p>
              ) : null}
              {briefingId ? (
                <ReasoningFeedback
                  briefingId={briefingId}
                  traceId={trace.trace_id}
                  entry={entry}
                />
              ) : null}
            </li>
          ))}
        </ol>
      ) : null}
    </div>
  );
}
