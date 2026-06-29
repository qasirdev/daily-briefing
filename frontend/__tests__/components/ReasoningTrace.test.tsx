import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { ReasoningTrace } from "@/components/ReasoningTrace";
import type { ReasoningTrace as ReasoningTraceData } from "@/lib/briefing-schema";

const trace: ReasoningTraceData = {
  trace_id: "b".repeat(32),
  hitl_mode: "human_in_the_loop",
  entries: [
    {
      agent_id: "focus",
      hitl_layer: "generator",
      status: "success",
      summary: "Built a focus plan from tasks and calendar.",
      execution_ms: 420,
      tokens_used: 88,
    },
  ],
};

describe("ReasoningTrace", () => {
  it("renders nothing when trace is empty", () => {
    const { container } = render(<ReasoningTrace trace={{ ...trace, entries: [] }} />);
    expect(container).toBeEmptyDOMElement();
  });

  it("expands trace entries and shows HITL mode", async () => {
    const user = userEvent.setup();
    render(<ReasoningTrace trace={trace} briefingId="brief-1" />);

    expect(screen.getByText("Agent reasoning trace")).toBeInTheDocument();
    expect(screen.getByText("Human-in-the-loop")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: /show 1 steps/i }));
    expect(screen.getByText(/Built a focus plan/i)).toBeInTheDocument();
    expect(screen.getByText(/420ms · 88 tokens/i)).toBeInTheDocument();
    expect(screen.getByText("Reasoning accurate?")).toBeInTheDocument();
  });

  it("collapses expanded trace", async () => {
    const user = userEvent.setup();
    render(<ReasoningTrace trace={trace} />);

    await user.click(screen.getByRole("button", { name: /show 1 steps/i }));
    expect(screen.getByText(/Built a focus plan/i)).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: /hide trace/i }));
    expect(screen.queryByText(/Built a focus plan/i)).not.toBeInTheDocument();
  });

  it("submits reasoning feedback when rated", async () => {
    const user = userEvent.setup();
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({ status: "saved" }),
      }),
    );

    render(<ReasoningTrace trace={trace} briefingId="brief-1" />);
    await user.click(screen.getByRole("button", { name: /show 1 steps/i }));
    await user.click(screen.getByRole("button", { name: "correct" }));

    expect(await screen.findByRole("status")).toHaveTextContent("Marked focus as correct");
  });
});
