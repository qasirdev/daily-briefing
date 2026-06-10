import { describe, expect, it } from "vitest";

import {
  briefingResponseSchema,
  formatCostUsd,
  isOrchestratorSummary,
  isSecurityBlockedBriefing,
  resolveBriefingAlertMessage,
  toObservabilityData,
} from "@/lib/briefing-schema";

const baseMetadata = {
  trace_id: "a".repeat(32),
  total_tokens: 0,
  total_cost_usd: 0,
  execution_ms: 0,
  model_used: "none",
  agents_invoked: [],
  agent_breakdown: [],
};

describe("resolveBriefingAlertMessage", () => {
  it("returns failure_message when provided", () => {
    const message = resolveBriefingAlertMessage(
      "failure",
      "security_violation_detected",
      "Briefing blocked: suspected prompt injection in calendar data.",
    );
    expect(message).toContain("calendar data");
  });

  it("returns security fallback when reason is security_violation_detected", () => {
    const message = resolveBriefingAlertMessage("failure", "security_violation_detected", null);
    expect(message).toContain("prompt injection");
  });

  it("returns degraded copy for degraded status", () => {
    const message = resolveBriefingAlertMessage("degraded", null, null);
    expect(message).toContain("degraded");
  });

  it("returns consent copy for awaiting_consent", () => {
    const message = resolveBriefingAlertMessage("awaiting_consent", null, null);
    expect(message).toContain("consent");
  });

  it("returns human review copy for awaiting_human_review", () => {
    const message = resolveBriefingAlertMessage("awaiting_human_review", null, null);
    expect(message).toContain("human review");
  });
});

describe("briefingResponseSchema", () => {
  it("accepts known failure_reason codes", () => {
    const parsed = briefingResponseSchema.parse({
      status: "failure",
      briefing: "",
      metadata: baseMetadata,
      failure_reason: "security_violation_detected",
      failure_message: "Briefing blocked.",
    });
    expect(parsed.failure_reason).toBe("security_violation_detected");
  });

  it("rejects unknown failure_reason values", () => {
    expect(() =>
      briefingResponseSchema.parse({
        status: "failure",
        briefing: "",
        metadata: baseMetadata,
        failure_reason: "not_a_real_reason",
      }),
    ).toThrow();
  });
});

describe("isSecurityBlockedBriefing", () => {
  it("detects security_violation_detected", () => {
    expect(isSecurityBlockedBriefing("security_violation_detected")).toBe(true);
    expect(isSecurityBlockedBriefing("token_budget_exceeded")).toBe(false);
    expect(isSecurityBlockedBriefing(null)).toBe(false);
  });
});

describe("formatCostUsd", () => {
  it("formats sub-cent and sub-dollar amounts", () => {
    expect(formatCostUsd(0)).toBe("$0");
    expect(formatCostUsd(0.004)).toBe("$0.0040");
    expect(formatCostUsd(0.45)).toBe("$0.450");
    expect(formatCostUsd(2.5)).toBe("$2.50");
  });
});

describe("toObservabilityData", () => {
  it("maps API metadata to observability view model", () => {
    const data = toObservabilityData(
      {
        ...baseMetadata,
        execution_ms: 900,
        total_tokens: 120,
        total_cost_usd: 0.03,
        model_used: "openai/gpt-4o-mini",
        agent_breakdown: [
          {
            agent_id: "focus",
            execution_ms: 800,
            tokens_used: 120,
            cost_usd: 0.03,
            model_used: "openai/gpt-4o-mini",
            status: "success",
          },
        ],
      },
      "success",
    );

    expect(data).toEqual({
      executionMs: 900,
      tokensUsed: 120,
      totalCostUsd: 0.03,
      modelUsed: "openai/gpt-4o-mini",
      status: "success",
      agentBreakdown: [
        expect.objectContaining({ agent_id: "focus", tokens_used: 120 }),
      ],
    });
  });
});

describe("isOrchestratorSummary", () => {
  it("detects orchestrator summary rows", () => {
    const row = {
      agent_id: "orchestrator",
      execution_ms: 0,
      tokens_used: 0,
      cost_usd: 0,
      model_used: "none",
      status: "success" as const,
    };
    expect(isOrchestratorSummary(row)).toBe(true);
    expect(isOrchestratorSummary({ ...row, agent_id: "focus" })).toBe(false);
  });
});

describe("resolveBriefingAlertMessage failure fallback", () => {
  it("returns generic failure copy", () => {
    expect(resolveBriefingAlertMessage("failure", null, null)).toContain("failed");
  });
});
