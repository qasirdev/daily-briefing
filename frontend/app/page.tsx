"use client";

import Link from "next/link";
import { useCallback, useState } from "react";

import { BriefingDashboard } from "@/components/BriefingDashboard";
import { ConsentPromptModal } from "@/components/ConsentPromptModal";
import {
  briefingResponseSchema,
  toObservabilityData,
  type BriefingResponse,
} from "@/lib/briefing-schema";
import { API_BASE, DEFAULT_USER_ID } from "@/lib/api";
import type { ConsentPromptRequest } from "@/lib/consent-schema";

const emptyObservability = {
  executionMs: 0,
  tokensUsed: 0,
  modelUsed: "none",
  status: "failure" as const,
  agentBreakdown: [],
};

export default function Home() {
  const [loading, setLoading] = useState(false);
  const [response, setResponse] = useState<BriefingResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [consentPrompt, setConsentPrompt] = useState<ConsentPromptRequest | null>(null);
  const [consentLoading, setConsentLoading] = useState(false);
  const [oauthError, setOauthError] = useState<string | null>(null);

  const generateBriefing = useCallback(async () => {
    setLoading(true);
    setError(null);
    setConsentPrompt(null);
    try {
      const res = await fetch(`${API_BASE}/api/v1/briefing/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: DEFAULT_USER_ID }),
      });
      const payload: unknown = await res.json();
      const parsed = briefingResponseSchema.parse(payload);
      setResponse(parsed);
      if (parsed.status === "awaiting_consent" && parsed.consent_request) {
        setConsentPrompt(parsed.consent_request);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to generate briefing");
    } finally {
      setLoading(false);
    }
  }, []);

  const handleGrantConsent = useCallback(
    async (ttlHours: number) => {
      if (!consentPrompt) {
        return;
      }
      setConsentLoading(true);
      setOauthError(null);
      try {
        const oauthRes = await fetch(
          `${API_BASE}/api/v1/consent/oauth/${consentPrompt.service}`,
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

        const grantRes = await fetch(`${API_BASE}/api/v1/consent`, {
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
        loading={loading && !response}
        onRetry={generateBriefing}
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
