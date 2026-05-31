import { z } from "zod";

export const consentRecordSchema = z.object({
  id: z.string().uuid(),
  user_id: z.string(),
  service: z.enum(["google_calendar", "postgres_mcp"]),
  scope: z.array(z.string()),
  agent_id: z.string(),
  consent_type: z.enum(["session", "time_bounded", "recurring"]),
  granted_at: z.string(),
  expires_at: z.string().nullable(),
  times_used: z.number().int().nonnegative(),
  last_used_at: z.string().nullable().optional(),
  revoked_at: z.string().nullable().optional(),
  revocation_reason: z.string().nullable().optional(),
});

export const consentPromptSchema = z.object({
  request_id: z.string(),
  service: z.enum(["google_calendar", "postgres_mcp"]),
  scope: z.array(z.string()),
  suggested_ttl_hours: z.number().int().nonnegative(),
  agent_requesting: z.string(),
  message: z.string(),
});

export const consentGrantSchema = z.object({
  user_id: z.string(),
  service: z.enum(["google_calendar", "postgres_mcp"]),
  scope: z.array(z.string()),
  agent_id: z.string().optional(),
  ttl_hours: z.number().int().nonnegative(),
  consent_type: z.enum(["session", "time_bounded", "recurring"]).optional(),
});

export type ConsentRecord = z.infer<typeof consentRecordSchema>;
export type ConsentPromptRequest = z.infer<typeof consentPromptSchema>;

export const SERVICE_LABELS: Record<ConsentPromptRequest["service"], string> = {
  google_calendar: "Google Calendar",
  postgres_mcp: "Task Database",
};

export const TTL_OPTIONS = [
  { label: "This briefing only", hours: 0 },
  { label: "1 hour", hours: 1 },
  { label: "4 hours", hours: 4 },
  { label: "24 hours", hours: 24 },
] as const;
