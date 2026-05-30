import { z } from "zod";

export const agentExecutionSummarySchema = z.object({
  agent_id: z.string(),
  execution_ms: z.number().int().nonnegative(),
  tokens_used: z.number().int().nonnegative(),
  model_used: z.string(),
  status: z.enum(["success", "failure", "escalated"]),
});

export const briefingMetadataSchema = z.object({
  trace_id: z.string(),
  total_tokens: z.number().int().nonnegative(),
  execution_ms: z.number().int().nonnegative(),
  model_used: z.string().default("none"),
  agents_invoked: z.array(z.string()),
  agent_breakdown: z.array(agentExecutionSummarySchema).default([]),
});

export const briefingResponseSchema = z.object({
  status: z.enum(["success", "degraded", "failure", "awaiting_consent"]),
  briefing: z.string(),
  metadata: briefingMetadataSchema,
  consent_context: z.string().nullable().optional(),
});

export type AgentExecutionSummary = z.infer<typeof agentExecutionSummarySchema>;
export type BriefingMetadata = z.infer<typeof briefingMetadataSchema>;
export type BriefingResponse = z.infer<typeof briefingResponseSchema>;

export type ObservabilityData = {
  executionMs: number;
  tokensUsed: number;
  modelUsed: string;
  status: "success" | "degraded" | "failure" | "awaiting_consent";
  agentBreakdown: AgentExecutionSummary[];
};

export function toObservabilityData(metadata: BriefingMetadata, status: BriefingResponse["status"]): ObservabilityData {
  return {
    executionMs: metadata.execution_ms,
    tokensUsed: metadata.total_tokens,
    modelUsed: metadata.model_used,
    status,
    agentBreakdown: metadata.agent_breakdown,
  };
}
