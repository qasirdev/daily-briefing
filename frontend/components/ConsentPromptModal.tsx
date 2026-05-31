"use client";

import { useState } from "react";

import {
  SERVICE_LABELS,
  TTL_OPTIONS,
  type ConsentPromptRequest,
} from "@/lib/consent-schema";

type ConsentPromptModalProps = {
  request: ConsentPromptRequest;
  isLoading?: boolean;
  oauthError?: string | null;
  onGrant: (ttlHours: number) => void;
  onDeny: () => void;
};

export function ConsentPromptModal({
  request,
  isLoading = false,
  oauthError = null,
  onGrant,
  onDeny,
}: ConsentPromptModalProps) {
  const [selectedTtl, setSelectedTtl] = useState(request.suggested_ttl_hours);

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby="consent-modal-title"
    >
      <div className="w-full max-w-md rounded-xl border border-black/10 bg-white p-6 shadow-xl dark:border-white/10 dark:bg-zinc-950">
        <h2 id="consent-modal-title" className="text-lg font-semibold text-foreground">
          Permission required
        </h2>
        <p className="mt-2 text-sm text-zinc-600 dark:text-zinc-300">
          The {request.agent_requesting} agent needs access to your{" "}
          {SERVICE_LABELS[request.service]}.
        </p>

        <div className="mt-4 space-y-3">
          <p className="text-sm font-medium">Requested permissions</p>
          <ul className="list-inside list-disc text-sm text-zinc-600 dark:text-zinc-300">
            {request.scope.map((scope) => (
              <li key={scope}>{scope}</li>
            ))}
          </ul>

          <label htmlFor="consent-ttl" className="block text-sm font-medium">
            Allow access for
          </label>
          <select
            id="consent-ttl"
            className="w-full rounded-md border border-black/15 bg-white px-3 py-2 text-sm dark:border-white/15 dark:bg-zinc-900"
            value={selectedTtl}
            onChange={(event) => setSelectedTtl(Number(event.target.value))}
            disabled={isLoading}
          >
            {TTL_OPTIONS.map((option) => (
              <option key={option.hours} value={option.hours}>
                {option.label}
              </option>
            ))}
          </select>
        </div>

        {oauthError ? (
          <p role="alert" className="mt-3 text-sm text-amber-700 dark:text-amber-400">
            {oauthError} If a popup was blocked, allow popups for this site and try again.
          </p>
        ) : null}

        <div className="mt-6 flex justify-end gap-3">
          <button
            type="button"
            className="rounded-md border border-black/15 px-4 py-2 text-sm dark:border-white/15"
            onClick={onDeny}
            disabled={isLoading}
          >
            Deny
          </button>
          <button
            type="button"
            className="rounded-md bg-briefing-primary px-4 py-2 text-sm font-medium text-white disabled:opacity-60"
            onClick={() => onGrant(selectedTtl)}
            disabled={isLoading}
          >
            {isLoading ? "Granting…" : "Allow"}
          </button>
        </div>
      </div>
    </div>
  );
}
