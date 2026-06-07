import { z } from "zod";

import { consentPromptSchema } from "@/lib/consent-schema";

export const reasoningTraceEntrySchema = z.object({
  agent_id: z.string(),
  hitl_layer: z.string(),
  summary: z.string(),
  status: z.enum(["success", "failure", "escalated", "awaiting_human"]),
  tokens_used: z.number().int().nonnegative(),
  execution_ms: z.number().int().nonnegative(),
});

export const reasoningTraceSchema = z.object({
  trace_id: z.string(),
  entries: z.array(reasoningTraceEntrySchema),
  hitl_mode: z.enum(["human_on_the_loop", "human_in_the_loop"]),
});

export const agentExecutionSummarySchema = z.object({
  agent_id: z.string(),
  execution_ms: z.number().int().nonnegative(),
  tokens_used: z.number().int().nonnegative(),
  cost_usd: z.number().nonnegative().default(0),
  model_used: z.string(),
  status: z.enum(["success", "failure", "escalated"]),
});

export const briefingMetadataSchema = z.object({
  trace_id: z.string(),
  total_tokens: z.number().int().nonnegative(),
  total_cost_usd: z.number().nonnegative().default(0),
  execution_ms: z.number().int().nonnegative(),
  model_used: z.string().default("none"),
  agents_invoked: z.array(z.string()),
  agent_breakdown: z.array(agentExecutionSummarySchema).default([]),
});

export const briefingResponseSchema = z.object({
  status: z.enum(["success", "degraded", "failure", "awaiting_consent", "awaiting_human_review"]),
  briefing: z.string(),
  metadata: briefingMetadataSchema,
  consent_context: z.string().nullable().optional(),
  consent_request: consentPromptSchema.nullable().optional(),
  reasoning_trace: reasoningTraceSchema.nullable().optional(),
});

export type ReasoningTraceEntry = z.infer<typeof reasoningTraceEntrySchema>;
export type ReasoningTrace = z.infer<typeof reasoningTraceSchema>;
export type AgentExecutionSummary = z.infer<typeof agentExecutionSummarySchema>;
export type BriefingMetadata = z.infer<typeof briefingMetadataSchema>;
export type BriefingResponse = z.infer<typeof briefingResponseSchema>;

export const ORCHESTRATOR_AGENT_ID = "orchestrator";

export type ObservabilityData = {
  executionMs: number;
  tokensUsed: number;
  totalCostUsd: number;
  modelUsed: string;
  status: "success" | "degraded" | "failure" | "awaiting_consent" | "awaiting_human_review";
  agentBreakdown: AgentExecutionSummary[];
};

export function isOrchestratorSummary(agent: AgentExecutionSummary): boolean {
  return agent.agent_id === ORCHESTRATOR_AGENT_ID;
}

export function formatCostUsd(costUsd: number): string {
  if (costUsd === 0) {
    return "$0";
  }
  if (costUsd < 0.01) {
    return `$${costUsd.toFixed(4)}`;
  }
  if (costUsd < 1) {
    return `$${costUsd.toFixed(3)}`;
  }
  return `$${costUsd.toFixed(2)}`;
}

export function toObservabilityData(metadata: BriefingMetadata, status: BriefingResponse["status"]): ObservabilityData {
  return {
    executionMs: metadata.execution_ms,
    tokensUsed: metadata.total_tokens,
    totalCostUsd: metadata.total_cost_usd,
    modelUsed: metadata.model_used,
    status,
    agentBreakdown: metadata.agent_breakdown,
  };
}
