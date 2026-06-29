import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { BriefingDashboard } from "@/components/BriefingDashboard";
import type { ObservabilityData } from "@/lib/briefing-schema";

const observability: ObservabilityData = {
  executionMs: 100,
  tokensUsed: 0,
  totalCostUsd: 0,
  modelUsed: "none",
  status: "failure",
  agentBreakdown: [],
};

describe("BriefingDashboard", () => {
  it("shows security block message without retry", () => {
    render(
      <BriefingDashboard
        briefing=""
        status="failure"
        observability={observability}
        failureReason="security_violation_detected"
        failureMessage="Briefing blocked: suspected prompt injection in calendar data."
        onRetry={vi.fn()}
      />,
    );

    const alert = screen.getByRole("alert");
    expect(alert).toHaveTextContent("calendar data");
    expect(alert.className).toMatch(/red/);
    expect(screen.queryByRole("button", { name: /retry/i })).not.toBeInTheDocument();
  });

  it("shows degraded state with retry option", () => {
    render(
      <BriefingDashboard
        briefing=""
        status="degraded"
        observability={{ ...observability, status: "degraded" }}
        onRetry={vi.fn()}
      />,
    );

    expect(screen.getByRole("alert")).toHaveTextContent("degraded");
    expect(screen.getByRole("button", { name: /retry/i })).toBeInTheDocument();
  });

  it("shows generic failure with retry", () => {
    render(
      <BriefingDashboard
        briefing=""
        status="failure"
        observability={observability}
        onRetry={vi.fn()}
      />,
    );

    expect(screen.getByRole("alert")).toHaveTextContent("failed");
    expect(screen.getByRole("button", { name: /retry/i })).toBeInTheDocument();
  });

  it("sanitizes HTML content before rendering", () => {
    render(
      <BriefingDashboard
        briefing="<script>alert('xss')</script><p>Safe content</p>"
        status="success"
        observability={{ ...observability, status: "success" }}
      />,
    );

    expect(screen.queryByText("alert('xss')")).not.toBeInTheDocument();
    expect(screen.getByText("Safe content")).toBeInTheDocument();
  });

  it("shows human review alert without retry", () => {
    render(
      <BriefingDashboard
        briefing=""
        status="awaiting_human_review"
        observability={{ ...observability, status: "awaiting_human_review" }}
      />,
    );

    expect(screen.getByRole("alert")).toHaveTextContent("human review");
    expect(screen.queryByRole("button", { name: /retry/i })).not.toBeInTheDocument();
  });

  it("renders loading skeleton when loading", () => {
    render(
      <BriefingDashboard
        briefing=""
        status="success"
        observability={{ ...observability, status: "success" }}
        loading
      />,
    );

    expect(screen.getByLabelText("Loading briefing")).toBeInTheDocument();
    expect(screen.queryByRole("article")).not.toBeInTheDocument();
  });

  it("renders briefing article when content exists", () => {
    render(
      <BriefingDashboard
        briefing="<p>Daily briefing</p>"
        status="success"
        observability={{ ...observability, status: "success" }}
      />,
    );

    expect(screen.getByRole("article", { name: "Daily briefing content" })).toBeInTheDocument();
    expect(screen.getByText("Daily briefing")).toBeInTheDocument();
  });
});
