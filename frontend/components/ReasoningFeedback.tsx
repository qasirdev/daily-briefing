"use client";

import { useState } from "react";

import { DEFAULT_USER_ID, getApiBase } from "@/lib/api";
import type { ReasoningTraceEntry } from "@/lib/briefing-schema";

type ReasoningFeedbackProps = {
  briefingId: string;
  traceId: string;
  entry: ReasoningTraceEntry;
};

type FeedbackRating = "correct" | "incorrect" | "partial";

export function ReasoningFeedback({ briefingId, traceId, entry }: ReasoningFeedbackProps) {
  const [status, setStatus] = useState<"idle" | "saving" | "saved" | "error">("idle");
  const [message, setMessage] = useState("");

  async function submitRating(rating: FeedbackRating) {
    setStatus("saving");
    setMessage("");
    try {
      const res = await fetch(`${getApiBase()}/api/v1/feedback/reasoning`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: DEFAULT_USER_ID,
          briefing_id: briefingId,
          trace_id: traceId,
          agent_id: entry.agent_id,
          rating,
          comment: "",
          hitl_layer: entry.hitl_layer,
        }),
      });
      if (!res.ok) {
        throw new Error(`Feedback failed (${res.status})`);
      }
      setStatus("saved");
      setMessage(`Marked ${entry.agent_id} as ${rating}`);
    } catch (err) {
      setStatus("error");
      setMessage(err instanceof Error ? err.message : "Feedback failed");
    }
  }

  return (
    <div className="mt-2 flex flex-wrap items-center gap-2">
      <span className="text-xs text-zinc-500">Reasoning accurate?</span>
      {(["correct", "partial", "incorrect"] as const).map((rating) => (
        <button
          key={rating}
          type="button"
          disabled={status === "saving" || status === "saved"}
          onClick={() => submitRating(rating)}
          className="rounded border border-black/10 px-2 py-0.5 text-xs capitalize disabled:opacity-50 dark:border-white/15"
        >
          {rating}
        </button>
      ))}
      {message ? (
        <span className="text-xs text-zinc-500" role="status">
          {message}
        </span>
      ) : null}
    </div>
  );
}
