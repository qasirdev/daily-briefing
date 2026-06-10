import { briefingResponseSchema, type BriefingResponse } from "@/lib/briefing-schema";

const LOCAL_DEV_BACKEND = "http://127.0.0.1:8010";

/** Ports where nginx serves both UI and /api on the same origin (Docker). */
const DOCKER_UI_PORTS = new Set(["8088", "80", "443"]);

/**
 * Resolve the FastAPI base URL at runtime.
 *
 * Priority:
 * 1. `NEXT_PUBLIC_API_BASE_URL` — explicit override (hybrid / custom setups)
 * 2. Browser on Docker/nginx port → same origin (e.g. http://localhost:8088)
 * 3. Default → local uvicorn on 8010 (Next.js dev on 3010)
 */
export function getApiBase(): string {
  const explicit = process.env.NEXT_PUBLIC_API_BASE_URL?.trim().replace(/\/$/, "");
  if (explicit) {
    return explicit;
  }

  if (typeof window !== "undefined") {
    const { port, origin, hostname } = window.location;
    if (DOCKER_UI_PORTS.has(port)) {
      return origin;
    }
    // Docker mapped to host port 80 — browser omits :80 from the URL
    if (
      port === "" &&
      (hostname === "localhost" || hostname === "127.0.0.1")
    ) {
      return origin;
    }
  }

  return LOCAL_DEV_BACKEND;
}

export const DEFAULT_USER_ID = "user-1";

export async function fetchBriefing(userId: string = DEFAULT_USER_ID): Promise<BriefingResponse> {
  const res = await fetch(`${getApiBase()}/api/v1/briefing/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ user_id: userId }),
  });
  const payload: unknown = await res.json();
  if (!res.ok) {
    const detail =
      typeof payload === "object" &&
      payload !== null &&
      "detail" in payload &&
      typeof payload.detail === "string"
        ? payload.detail
        : `Briefing request failed (${res.status})`;
    throw new Error(detail);
  }
  return briefingResponseSchema.parse(payload);
}
