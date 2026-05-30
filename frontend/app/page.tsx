"use client";

import { useCallback, useState } from "react";

import { BriefingDashboard } from "@/components/BriefingDashboard";
import {
  briefingResponseSchema,
  toObservabilityData,
  type BriefingResponse,
} from "@/lib/briefing-schema";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";

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

  const generateBriefing = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_BASE}/api/v1/briefing/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: "user-1" }),
      });
      const payload: unknown = await res.json();
      const parsed = briefingResponseSchema.parse(payload);
      setResponse(parsed);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to generate briefing");
    } finally {
      setLoading(false);
    }
  }, []);

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
        <button
          type="button"
          onClick={generateBriefing}
          disabled={loading}
          className="rounded-lg bg-briefing-primary px-4 py-2 text-sm font-medium text-white disabled:opacity-60"
        >
          {loading ? "Generating…" : "Generate briefing"}
        </button>
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
    </main>
  );
}
