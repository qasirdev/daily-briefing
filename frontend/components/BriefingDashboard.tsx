"use client";

import { useMemo } from "react";

import { ObservabilityBadge } from "@/components/ObservabilityBadge";
import { sanitizeHtml } from "@/lib/sanitize";
import {
  isSecurityBlockedBriefing,
  resolveBriefingAlertMessage,
  type ObservabilityData,
} from "@/lib/briefing-schema";
import type { AccountUsage } from "@/lib/account-usage";
import type { VisitUsageStats } from "@/lib/cost-tracking";

type BriefingDashboardProps = {
  briefing: string;
  status: ObservabilityData["status"];
  observability: ObservabilityData;
  visitStats?: VisitUsageStats | null;
  accountUsage?: AccountUsage | null;
  loading?: boolean;
  onRetry?: () => void;
  failureReason?: string | null;
  failureMessage?: string | null;
};

export function BriefingDashboard({
  briefing,
  status,
  observability,
  visitStats = null,
  accountUsage = null,
  loading = false,
  onRetry,
  failureReason = null,
  failureMessage = null,
}: BriefingDashboardProps) {
  const sanitizedHtml = useMemo(() => sanitizeHtml(briefing), [briefing]);

  const showDegradedAlert =
    status === "degraded" ||
    status === "failure" ||
    status === "awaiting_consent" ||
    status === "awaiting_human_review";
  const isSecurityBlock = isSecurityBlockedBriefing(failureReason);
  const alertMessage = resolveBriefingAlertMessage(status, failureReason, failureMessage);

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
          className={
            isSecurityBlock
              ? "rounded-lg border border-red-300 bg-red-50 px-4 py-3 text-red-900 dark:border-red-700 dark:bg-red-950/40 dark:text-red-100"
              : "rounded-lg border border-amber-300 bg-amber-50 px-4 py-3 text-amber-900 dark:border-amber-700 dark:bg-amber-950/40 dark:text-amber-100"
          }
        >
          {alertMessage}
          {onRetry && !isSecurityBlock ? (
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

      <ObservabilityBadge
        data={observability}
        visitStats={visitStats}
        accountUsage={accountUsage}
      />
    </section>
  );
}
