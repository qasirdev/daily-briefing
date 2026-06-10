import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import { ObservabilityBadge } from "@/components/ObservabilityBadge";
import type { ObservabilityData } from "@/lib/briefing-schema";

const baseData: ObservabilityData = {
  executionMs: 1200,
  tokensUsed: 500,
  totalCostUsd: 0.01,
  modelUsed: "openai/gpt-oss-120b:free",
  status: "success",
  agentBreakdown: [
    {
      agent_id: "focus",
      execution_ms: 800,
      tokens_used: 500,
      cost_usd: 0.01,
      model_used: "deepseek/deepseek-v4-flash",
      status: "success",
    },
  ],
};

describe("ObservabilityBadge", () => {
  it("renders execution metrics", () => {
    render(<ObservabilityBadge data={baseData} />);
    expect(screen.getByLabelText(/Execution time/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Tokens used/i)).toHaveTextContent("500");
  });

  it("shows failure status styling label", () => {
    render(<ObservabilityBadge data={{ ...baseData, status: "failure" }} />);
    expect(screen.getByText("failure")).toBeInTheDocument();
  });

  it("expands agent breakdown on toggle", async () => {
    const user = userEvent.setup();
    render(<ObservabilityBadge data={baseData} />);
    await user.click(screen.getByRole("button", { name: /show agents/i }));
    expect(screen.getByText("focus")).toBeInTheDocument();
  });

  it("shows visit and account usage summaries", () => {
    render(
      <ObservabilityBadge
        data={{ ...baseData, status: "degraded" }}
        visitStats={{
          runsSinceLastVisit: 2,
          costSinceLastVisit: 0.02,
          tokensSinceLastVisit: 100,
          visitAvgCostPerRun: 0.01,
          lifetimeRuns: 5,
          lifetimeCostUsd: 0.05,
          lifetimeTokens: 500,
          lifetimeAvgCostPerRun: 0.01,
        }}
        accountUsage={{
          available: true,
          source: "openrouter_key",
          label: "dev",
          fetched_at: new Date().toISOString(),
          usage_monthly_usd: 0.12,
          limit_remaining_usd: 4.5,
        }}
      />,
    );

    expect(screen.getByText(/This visit: 2 runs/i)).toBeInTheDocument();
    expect(screen.getByText(/Lifetime \(this browser\): 5 runs/i)).toBeInTheDocument();
    expect(screen.getByText(/OpenRouter account \(dev\)/i)).toBeInTheDocument();
    expect(screen.getByText(/remaining/i)).toBeInTheDocument();
    expect(screen.getByText(/Degraded/i)).toBeInTheDocument();
  });

  it("labels orchestrator row as session total", async () => {
    const user = userEvent.setup();
    render(
      <ObservabilityBadge
        data={{
          ...baseData,
          agentBreakdown: [
            ...baseData.agentBreakdown,
            {
              agent_id: "orchestrator",
              execution_ms: 10,
              tokens_used: 500,
              cost_usd: 0,
              model_used: "none",
              status: "success",
            },
          ],
        }}
      />,
    );

    await user.click(screen.getByRole("button", { name: /show agents/i }));
    expect(screen.getByText(/session total \(not billed\)/i)).toBeInTheDocument();
  });
});
