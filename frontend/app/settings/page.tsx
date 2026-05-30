"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import { API_BASE, DEFAULT_USER_ID } from "@/lib/api";
import { consentRecordSchema, type ConsentRecord } from "@/lib/consent-schema";

async function fetchConsents(): Promise<ConsentRecord[]> {
  const res = await fetch(
    `${API_BASE}/api/v1/consent?user_id=${encodeURIComponent(DEFAULT_USER_ID)}`,
  );
  if (!res.ok) {
    throw new Error(`Failed to load consents (${res.status})`);
  }
  const payload: unknown = await res.json();
  return consentRecordSchema.array().parse(payload);
}

export default function SettingsPage() {
  const [consents, setConsents] = useState<ConsentRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [confirmId, setConfirmId] = useState<string | null>(null);
  const [revoking, setRevoking] = useState<string | null>(null);

  const refreshConsents = useCallback(async () => {
    setError(null);
    setLoading(true);
    try {
      setConsents(await fetchConsents());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load consents");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    let active = true;
    fetchConsents()
      .then((records) => {
        if (active) {
          setConsents(records);
        }
      })
      .catch((err: unknown) => {
        if (active) {
          setError(err instanceof Error ? err.message : "Failed to load consents");
        }
      })
      .finally(() => {
        if (active) {
          setLoading(false);
        }
      });
    return () => {
      active = false;
    };
  }, []);

  const revokeConsent = async (consentId: string) => {
    setRevoking(consentId);
    setError(null);
    try {
      const res = await fetch(`${API_BASE}/api/v1/consent/${consentId}`, {
        method: "DELETE",
      });
      if (!res.ok) {
        throw new Error(`Revoke failed (${res.status})`);
      }
      setConfirmId(null);
      await refreshConsents();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to revoke consent");
    } finally {
      setRevoking(null);
    }
  };

  return (
    <main className="mx-auto flex min-h-full w-full max-w-3xl flex-col gap-6 px-6 py-16">
      <header className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="text-sm font-medium uppercase tracking-wide text-briefing-primary">
            Settings
          </p>
          <h1 className="mt-2 text-3xl font-semibold tracking-tight text-foreground">
            Consent dashboard
          </h1>
        </div>
        <Link href="/" className="text-sm text-briefing-primary underline-offset-2 hover:underline">
          Back to briefing
        </Link>
      </header>

      <section className="rounded-xl border border-black/10 bg-white p-6 shadow-sm dark:border-white/10 dark:bg-zinc-950">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <h2 className="text-lg font-medium">Active consents</h2>
          <div className="flex gap-3">
            <button
              type="button"
              className="text-sm text-zinc-600 underline-offset-2 hover:underline dark:text-zinc-300"
              onClick={() => void refreshConsents()}
            >
              Refresh
            </button>
            <a
              href={`${API_BASE}/api/v1/export?user_id=${encodeURIComponent(DEFAULT_USER_ID)}&format=json`}
              className="text-sm text-briefing-primary underline-offset-2 hover:underline"
            >
              Export my data
            </a>
          </div>
        </div>

        {error ? (
          <p role="alert" className="mt-4 text-sm text-red-600">
            {error}
          </p>
        ) : null}

        {loading ? (
          <p className="mt-4 text-sm text-zinc-500">Loading consents…</p>
        ) : consents.length === 0 ? (
          <p className="mt-4 text-sm text-zinc-500">
            No active consents. Generate a briefing to grant calendar access when prompted.
          </p>
        ) : (
          <ul className="mt-4 max-h-96 space-y-3 overflow-y-auto">
            {consents.map((consent) => (
              <li
                key={consent.id}
                className="rounded-lg border border-black/10 p-4 dark:border-white/10"
              >
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <p className="font-medium capitalize">{consent.service.replace("_", " ")}</p>
                    <p className="text-sm text-zinc-500">
                      Granted {new Date(consent.granted_at).toLocaleString()}
                      {consent.expires_at
                        ? ` · Expires ${new Date(consent.expires_at).toLocaleString()}`
                        : " · No expiry"}
                    </p>
                    <p className="mt-1 text-sm text-zinc-600 dark:text-zinc-300">
                      Used {consent.times_used} times
                    </p>
                    <p className="text-xs text-zinc-500">{consent.scope.join(", ")}</p>
                  </div>
                  {confirmId === consent.id ? (
                    <div className="flex gap-2">
                      <button
                        type="button"
                        className="rounded-md border px-3 py-1 text-sm"
                        onClick={() => setConfirmId(null)}
                      >
                        Cancel
                      </button>
                      <button
                        type="button"
                        className="rounded-md bg-red-600 px-3 py-1 text-sm text-white disabled:opacity-60"
                        disabled={revoking === consent.id}
                        onClick={() => void revokeConsent(consent.id)}
                      >
                        Confirm revoke
                      </button>
                    </div>
                  ) : (
                    <button
                      type="button"
                      className="rounded-md border border-red-300 px-3 py-1 text-sm text-red-700 dark:border-red-800 dark:text-red-400"
                      onClick={() => setConfirmId(consent.id)}
                    >
                      Revoke
                    </button>
                  )}
                </div>
              </li>
            ))}
          </ul>
        )}
      </section>
    </main>
  );
}
