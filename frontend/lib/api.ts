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
