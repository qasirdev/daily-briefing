import { z } from "zod";

import { getApiBase } from "@/lib/api";

export const accountUsageSchema = z.object({
  available: z.boolean(),
  source: z.enum(["openrouter_key", "unavailable"]).default("unavailable"),
  label: z.string().nullable().optional(),
  usage_all_time_usd: z.number().nonnegative().nullable().optional(),
  usage_daily_usd: z.number().nonnegative().nullable().optional(),
  usage_weekly_usd: z.number().nonnegative().nullable().optional(),
  usage_monthly_usd: z.number().nonnegative().nullable().optional(),
  limit_remaining_usd: z.number().nonnegative().nullable().optional(),
  is_free_tier: z.boolean().nullable().optional(),
  fetched_at: z.string(),
  message: z.string().nullable().optional(),
});

export type AccountUsage = z.infer<typeof accountUsageSchema>;

export async function fetchAccountUsage(): Promise<AccountUsage | null> {
  try {
    const res = await fetch(`${getApiBase()}/api/v1/usage/account`);
    if (!res.ok) {
      return null;
    }
    const payload: unknown = await res.json();
    return accountUsageSchema.parse(payload);
  } catch {
    return null;
  }
}

export function formatAccountUsageSummary(usage: AccountUsage): string {
  if (!usage.available) {
    return usage.message ?? "OpenRouter account usage unavailable";
  }

  const parts: string[] = [];
  if (usage.usage_all_time_usd != null) {
    parts.push(`all-time ${formatUsd(usage.usage_all_time_usd)}`);
  }
  if (usage.usage_monthly_usd != null) {
    parts.push(`this month ${formatUsd(usage.usage_monthly_usd)}`);
  }
  if (usage.usage_daily_usd != null) {
    parts.push(`today ${formatUsd(usage.usage_daily_usd)}`);
  }
  if (parts.length === 0) {
    return "OpenRouter account usage available";
  }
  return parts.join(" · ");
}

function formatUsd(amount: number): string {
  if (amount < 0.01) {
    return `$${amount.toFixed(4)}`;
  }
  if (amount < 1) {
    return `$${amount.toFixed(3)}`;
  }
  return `$${amount.toFixed(2)}`;
}
