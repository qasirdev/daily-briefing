import { act, renderHook, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { useBriefing } from "@/hooks/useBriefing";
import type { BriefingResponse } from "@/lib/briefing-schema";

vi.mock("@/lib/api", () => ({
  DEFAULT_USER_ID: "user-1",
  fetchBriefing: vi.fn(),
}));

import { fetchBriefing } from "@/lib/api";

const mockFetchBriefing = vi.mocked(fetchBriefing);

const successResponse: BriefingResponse = {
  status: "success",
  briefing: "<p>Hello</p>",
  metadata: {
    trace_id: "a".repeat(32),
    total_tokens: 120,
    total_cost_usd: 0.01,
    execution_ms: 500,
    model_used: "openai/gpt-4o-mini",
    agents_invoked: ["focus"],
    agent_breakdown: [],
  },
};

describe("useBriefing", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("starts with idle state", () => {
    const { result } = renderHook(() => useBriefing());

    expect(result.current.data).toBeNull();
    expect(result.current.isLoading).toBe(false);
    expect(result.current.error).toBeNull();
  });

  it("loads briefing data on refetch", async () => {
    mockFetchBriefing.mockResolvedValueOnce(successResponse);

    const { result } = renderHook(() => useBriefing());

    await act(async () => {
      await result.current.refetch();
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.data).toEqual(successResponse);
    expect(result.current.error).toBeNull();
    expect(mockFetchBriefing).toHaveBeenCalledWith("user-1");
  });

  it("surfaces errors when fetch fails", async () => {
    mockFetchBriefing.mockRejectedValueOnce(new Error("Network error"));

    const { result } = renderHook(() => useBriefing());

    await act(async () => {
      await result.current.refetch();
    });

    expect(result.current.data).toBeNull();
    expect(result.current.error).toBe("Network error");
  });

  it("preserves security failure response without throwing", async () => {
    const securityFailure: BriefingResponse = {
      status: "failure",
      briefing: "",
      metadata: {
        trace_id: "b".repeat(32),
        total_tokens: 0,
        total_cost_usd: 0,
        execution_ms: 50,
        model_used: "none",
        agents_invoked: ["input_security_gate"],
        agent_breakdown: [],
      },
      failure_reason: "security_violation_detected",
      failure_message: "Briefing blocked: suspected prompt injection in calendar data.",
    };
    mockFetchBriefing.mockResolvedValueOnce(securityFailure);

    const { result } = renderHook(() => useBriefing());

    await act(async () => {
      await result.current.refetch();
    });

    expect(result.current.data?.failure_reason).toBe("security_violation_detected");
    expect(result.current.data?.failure_message).toContain("calendar data");
    expect(result.current.error).toBeNull();
  });

  it("invokes onSuccess after a successful refetch", async () => {
    mockFetchBriefing.mockResolvedValueOnce(successResponse);
    const onSuccess = vi.fn();

    const { result } = renderHook(() => useBriefing({ onSuccess }));

    await act(async () => {
      await result.current.refetch();
    });

    expect(onSuccess).toHaveBeenCalledWith(successResponse);
  });
});
