"use client";

import DOMPurify from "dompurify";
import { useMemo } from "react";

import { ObservabilityBadge } from "@/components/ObservabilityBadge";
import type { ObservabilityData } from "@/lib/briefing-schema";

type BriefingDashboardProps = {
  briefing: string;
  status: ObservabilityData["status"];
  observability: ObservabilityData;
  loading?: boolean;
  onRetry?: () => void;
};

export function BriefingDashboard({
  briefing,
  status,
  observability,
  loading = false,
  onRetry,
}: BriefingDashboardProps) {
  const sanitizedHtml = useMemo(() => {
    if (!briefing.trim()) {
      return "";
    }
    return DOMPurify.sanitize(briefing, { USE_PROFILES: { html: true } });
  }, [briefing]);

  const showDegradedAlert = status === "degraded" || status === "failure" || status === "awaiting_consent";

  if (loading) {
    return (
      <section aria-busy="true" aria-label="Loading briefing" className="space-y-4">
        <div className="h-8 w-2/3 animate-pulse rounded bg-zinc-200 dark:bg-zinc-800" />
        <div className="h-32 animate-pulse rounded-xl bg-zinc-200 dark:bg-zinc-800" />
        <div className="h-20 animate-pulse rounded-lg bg-zinc-200 dark:bg-zinc-800" />
      </section>
    );
  }

  return (
    <section className="space-y-6" aria-label="Briefing dashboard">
      {showDegradedAlert ? (
        <div
          role="alert"
          className="rounded-lg border border-amber-300 bg-amber-50 px-4 py-3 text-amber-900 dark:border-amber-700 dark:bg-amber-950/40 dark:text-amber-100"
        >
          {status === "awaiting_consent"
            ? "Calendar access requires consent before a full briefing can be generated."
            : "Some briefing components were degraded. Review the observability details below."}
          {onRetry ? (
            <button
              type="button"
              className="ml-3 rounded-md bg-amber-800 px-3 py-1 text-sm text-white hover:bg-amber-900"
              onClick={onRetry}
            >
              Retry
            </button>
          ) : null}
        </div>
      ) : null}

      <article
        className="prose prose-zinc max-h-[32rem] max-w-none overflow-y-auto rounded-xl border border-black/10 bg-white p-6 shadow-sm dark:prose-invert dark:border-white/10 dark:bg-zinc-950"
        aria-label="Daily briefing content"
      >
        {sanitizedHtml ? (
          <div dangerouslySetInnerHTML={{ __html: sanitizedHtml }} />
        ) : (
          <p className="text-zinc-500">No briefing content yet. Generate a briefing to see results here.</p>
        )}
      </article>

      <ObservabilityBadge data={observability} />
    </section>
  );
}
