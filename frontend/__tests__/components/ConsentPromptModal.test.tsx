import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { ConsentPromptModal } from "@/components/ConsentPromptModal";
import type { ConsentPromptRequest } from "@/lib/consent-schema";

const request: ConsentPromptRequest = {
  request_id: "req-1",
  service: "google_calendar",
  scope: ["calendar.readonly"],
  suggested_ttl_hours: 4,
  agent_requesting: "calendar",
  message: "Calendar access is required for today's events.",
};

describe("ConsentPromptModal", () => {
  it("renders dialog with service and scopes", () => {
    render(
      <ConsentPromptModal request={request} onGrant={vi.fn()} onDeny={vi.fn()} />,
    );
    expect(screen.getByRole("dialog")).toBeInTheDocument();
    expect(screen.getByText(/Google Calendar/i)).toBeInTheDocument();
    expect(screen.getByText("calendar.readonly")).toBeInTheDocument();
  });

  it("calls onGrant with selected ttl", async () => {
    const user = userEvent.setup();
    const onGrant = vi.fn();
    render(
      <ConsentPromptModal request={request} onGrant={onGrant} onDeny={vi.fn()} />,
    );
    await user.click(screen.getByRole("button", { name: /allow/i }));
    expect(onGrant).toHaveBeenCalledWith(4);
  });

  it("calls onDeny when denied", async () => {
    const user = userEvent.setup();
    const onDeny = vi.fn();
    render(
      <ConsentPromptModal request={request} onGrant={vi.fn()} onDeny={onDeny} />,
    );
    await user.click(screen.getByRole("button", { name: /deny/i }));
    expect(onDeny).toHaveBeenCalledOnce();
  });

  it("shows oauth error alert and loading state", () => {
    render(
      <ConsentPromptModal
        request={request}
        isLoading
        oauthError="OAuth popup was blocked."
        onGrant={vi.fn()}
        onDeny={vi.fn()}
      />,
    );
    expect(screen.getByRole("alert")).toHaveTextContent("OAuth popup was blocked.");
    expect(screen.getByRole("button", { name: /granting/i })).toBeDisabled();
  });

  it("renders machine action payload when present", () => {
    render(
      <ConsentPromptModal
        request={{
          ...request,
          action_payload: { tool: "calendar.read_events", date: "2026-06-10" },
        }}
        onGrant={vi.fn()}
        onDeny={vi.fn()}
      />,
    );
    expect(screen.getByText(/Machine action/i)).toBeInTheDocument();
    expect(screen.getByText(/calendar.read_events/)).toBeInTheDocument();
  });

  it("calls onGrant with custom ttl from select", async () => {
    const user = userEvent.setup();
    const onGrant = vi.fn();
    render(
      <ConsentPromptModal request={request} onGrant={onGrant} onDeny={vi.fn()} />,
    );
    await user.selectOptions(screen.getByLabelText(/allow access for/i), "24");
    await user.click(screen.getByRole("button", { name: /allow/i }));
    expect(onGrant).toHaveBeenCalledWith(24);
  });
});
