"use client";

import Link from "next/link";
import { useCallback, useEffect, useRef, useState } from "react";

import { BriefingDashboard } from "@/components/BriefingDashboard";
import { ConsentPromptModal } from "@/components/ConsentPromptModal";
import { ReasoningTrace } from "@/components/ReasoningTrace";
import {
  briefingResponseSchema,
  toObservabilityData,
  type BriefingResponse,
  type ObservabilityData,
} from "@/lib/briefing-schema";
import { fetchAccountUsage, type AccountUsage } from "@/lib/account-usage";
import { DEFAULT_USER_ID, getApiBase } from "@/lib/api";
import type { ConsentPromptRequest } from "@/lib/consent-schema";
import {
  computeVisitStats,
  readUsageTracking,
  recordBriefingUsage,
  type UsageTracking,
  type VisitUsageStats,
} from "@/lib/cost-tracking";

const emptyObservability: ObservabilityData = {
  executionMs: 0,
  tokensUsed: 0,
  totalCostUsd: 0,
  modelUsed: "none",
  status: "failure",
  agentBreakdown: [],
};

export default function Home() {
  const [loading, setLoading] = useState(false);
  const [response, setResponse] = useState<BriefingResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [consentPrompt, setConsentPrompt] = useState<ConsentPromptRequest | null>(null);
  const [consentLoading, setConsentLoading] = useState(false);
  const [oauthError, setOauthError] = useState<string | null>(null);
  const [visitStats, setVisitStats] = useState<VisitUsageStats | null>(null);
  const [accountUsage, setAccountUsage] = useState<AccountUsage | null>(null);
  const visitBaselineRef = useRef<UsageTracking | null>(null);

  const refreshAccountUsage = useCallback(async () => {
    const usage = await fetchAccountUsage();
    setAccountUsage(usage);
  }, []);

  useEffect(() => {
    visitBaselineRef.current = readUsageTracking();
    const baseline = visitBaselineRef.current;
    setVisitStats(computeVisitStats(baseline, baseline));
    void refreshAccountUsage();
  }, [refreshAccountUsage]);

  const generateBriefing = useCallback(async () => {
    setLoading(true);
    setError(null);
    setConsentPrompt(null);
    try {
      const res = await fetch(`${getApiBase()}/api/v1/briefing/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: DEFAULT_USER_ID }),
      });
      const payload: unknown = await res.json();
      const parsed = briefingResponseSchema.parse(payload);
      setResponse(parsed);
      const tracking = recordBriefingUsage(
        parsed.metadata.total_cost_usd,
        parsed.metadata.total_tokens,
      );
      const baseline = visitBaselineRef.current ?? readUsageTracking();
      setVisitStats(computeVisitStats(baseline, tracking));
      void refreshAccountUsage();
      if (parsed.status === "awaiting_consent" && parsed.consent_request) {
        setConsentPrompt(parsed.consent_request);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to generate briefing");
    } finally {
      setLoading(false);
    }
  }, [refreshAccountUsage]);

  const handleGrantConsent = useCallback(
    async (ttlHours: number) => {
      if (!consentPrompt) {
        return;
      }
      setConsentLoading(true);
      setOauthError(null);
      try {
        const oauthRes = await fetch(
          `${getApiBase()}/api/v1/consent/oauth/${consentPrompt.service}`,
        );
        if (oauthRes.ok) {
          const oauthPayload: { oauth_url?: string } = await oauthRes.json();
          if (oauthPayload.oauth_url) {
            const popup = window.open(oauthPayload.oauth_url, "_blank", "noopener,noreferrer");
            if (!popup) {
              setOauthError("OAuth popup was blocked.");
            }
          }
        }

        const grantRes = await fetch(`${getApiBase()}/api/v1/consent`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            user_id: DEFAULT_USER_ID,
            service: consentPrompt.service,
            scope: consentPrompt.scope,
            agent_id: consentPrompt.agent_requesting,
            ttl_hours: ttlHours,
          }),
        });
        if (!grantRes.ok) {
          throw new Error(`Consent grant failed (${grantRes.status})`);
        }

        setConsentPrompt(null);
        await generateBriefing();
      } catch (err) {
        setOauthError(err instanceof Error ? err.message : "Consent grant failed");
      } finally {
        setConsentLoading(false);
      }
    },
    [consentPrompt, generateBriefing],
  );

  const observability = response
    ? toObservabilityData(response.metadata, response.status)
    : emptyObservability;

  return (
    <main className="mx-auto flex min-h-full w-full max-w-3xl flex-col gap-6 px-6 py-16">
      <header className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="text-sm font-medium uppercase tracking-wide text-briefing-primary">
            AI Daily Briefing Assistant
          </p>
          <h1 className="mt-2 text-4xl font-semibold tracking-tight text-foreground">
            Daily Briefing
          </h1>
        </div>
        <div className="flex gap-3">
          <Link
            href="/settings"
            className="rounded-lg border border-black/15 px-4 py-2 text-sm dark:border-white/15"
          >
            Settings
          </Link>
          <button
            type="button"
            onClick={generateBriefing}
            disabled={loading || consentLoading}
            className="rounded-lg bg-briefing-primary px-4 py-2 text-sm font-medium text-white disabled:opacity-60"
          >
            {loading ? "Generating…" : "Generate briefing"}
          </button>
        </div>
      </header>

      {error ? (
        <p role="alert" className="text-red-600">
          {error}
        </p>
      ) : null}

      <BriefingDashboard
        briefing={response?.briefing ?? ""}
        status={response?.status ?? "failure"}
        observability={observability}
        visitStats={visitStats}
        accountUsage={accountUsage}
        loading={loading && !response}
        onRetry={generateBriefing}
      />

      <ReasoningTrace
        trace={response?.reasoning_trace ?? null}
        briefingId={response?.metadata.trace_id}
      />

      {consentPrompt ? (
        <ConsentPromptModal
          request={consentPrompt}
          isLoading={consentLoading}
          oauthError={oauthError}
          onGrant={handleGrantConsent}
          onDeny={() => setConsentPrompt(null)}
        />
      ) : null}
    </main>
  );
}
