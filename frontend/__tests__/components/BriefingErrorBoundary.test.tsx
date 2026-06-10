import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { BriefingErrorBoundary } from "@/components/BriefingErrorBoundary";

function ThrowingChild({ shouldThrow }: { shouldThrow: boolean }) {
  if (shouldThrow) {
    throw new Error("Render failed");
  }
  return <p>Briefing content</p>;
}

describe("BriefingErrorBoundary", () => {
  it("renders children when no error occurs", () => {
    render(
      <BriefingErrorBoundary>
        <p>Briefing content</p>
      </BriefingErrorBoundary>,
    );

    expect(screen.getByText("Briefing content")).toBeInTheDocument();
  });

  it("shows accessible fallback when a child throws", () => {
    const consoleError = vi.spyOn(console, "error").mockImplementation(() => {});

    render(
      <BriefingErrorBoundary>
        <ThrowingChild shouldThrow />
      </BriefingErrorBoundary>,
    );

    expect(screen.getByRole("alert")).toBeInTheDocument();
    expect(screen.getByText("Render failed")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /try again/i })).toBeInTheDocument();

    consoleError.mockRestore();
  });

  it("invokes onReset when Try again is clicked", async () => {
    const consoleError = vi.spyOn(console, "error").mockImplementation(() => {});
    const onReset = vi.fn();
    const user = userEvent.setup();

    render(
      <BriefingErrorBoundary onReset={onReset}>
        <ThrowingChild shouldThrow />
      </BriefingErrorBoundary>,
    );

    await user.click(screen.getByRole("button", { name: /try again/i }));

    expect(onReset).toHaveBeenCalledTimes(1);

    consoleError.mockRestore();
  });
});
