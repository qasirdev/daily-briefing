# Try It Locally — AI Daily Briefing Assistant

**Version:** 1.4.0 | **Last Updated:** May 2026

This guide walks through running the project on your machine: backend only, frontend only, or the full Docker stack.

For **MVP 1 (Epic DB-E1)** scaffold-only behavior, see [Epic E1 branch](#epic-e1-branch-mvp-1-scaffold) below.

---

## Prerequisites

| Tool | Version | Check |
|---|---|---|
| [uv](https://docs.astral.sh/uv/) | >= 0.5 | `uv --version` |
| Python | 3.12+ (uv manages the venv) | `uv run python --version` |
| Node.js | 22.x | `nvm use` (reads `.nvmrc`) |
| Docker | 27+ (optional, full stack) | `docker --version` |

---

## 1. Environment setup

From the repo root:

```bash
cp .env.example .env
```

Edit `.env` as needed:

- **`OPENROUTER_API_KEY`** — required for the Focus agent LLM calls (MVP 2+). Leave empty only if you are testing health checks or mocked flows.
- **`LOCAL_LLM_ENABLED=true`** — optional fallback when OpenRouter is unavailable.
- **`POSTGRES_MCP_*` / `CALENDAR_MCP_*`** — MCP server host/port (defaults: `5433` and `5434`).
- **`ADMIN_API_KEY`** — required for DLQ admin endpoints (MVP 3+). See [Local notes (MVP 3+)](#local-notes-mvp-3).
- **`OTEL_EXPORTER_OTLP_ENDPOINT`** — optional OpenTelemetry collector (default `http://localhost:4317`).
- **`LOCAL_LLM_MODEL_ID`** — local model id when `LOCAL_LLM_ENABLED=true` (MVP 4+). See [docs/LOCAL-LLM.md](../LOCAL-LLM.md).
- **`GOOGLE_OAUTH_AUTHORIZE_URL`** — optional OAuth URL for Google Calendar JIT consent (MVP 4+).

---

## 2. Backend (FastAPI + LangGraph)

```bash
uv sync --all-extras
uv run uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

Use **`8000`**, not `800`. Ports below 1024 require root on macOS and cause `Permission denied`.

### Health check

```bash
curl http://127.0.0.1:8000/health
```

Expected:

```json
{"status":"healthy","version":"0.1.0"}
```

### Generate a briefing (MVP 2+)

Start the backend first (see [§2 Backend](#2-backend-fastapi--langgraph)), then:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/briefing/generate \
  -H "Content-Type: application/json" \
  -d '{"user_id":"user-1"}'
```

Response includes `X-Trace-Id` in headers.

#### After pulling code changes

If you previously saw `Internal Server Error`, restart uvicorn so it loads the latest code (`--reload` may not always pick up every change):

```bash
# Stop the running server (Ctrl+C), then:
uv sync --all-extras
uv run uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

Retry the briefing request:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/briefing/generate \
  -H "Content-Type: application/json" \
  -d '{"user_id":"user-1"}'
```

#### Expected without MCP / LLM (local smoke test)

If PostgreSQL MCP (`5433`), Calendar MCP (`5434`), and OpenRouter are **not** running, a **200** response with `"status": "degraded"` is normal — not a failure:

```json
{
  "status": "degraded",
  "briefing": "<h1>Daily Briefing</h1><p><strong>Note:</strong> Some components were degraded.</p>",
  "metadata": {
    "trace_id": "...",
    "total_tokens": 0,
    "execution_ms": 1700,
    "agents_invoked": ["task", "calendar", "focus", "critic", "orchestrator"]
  },
  "consent_context": null
}
```

#### Full briefing (live data)

For tasks, calendar events, and an LLM-generated focus plan you need:

| Dependency | `.env` / setup |
|---|---|
| PostgreSQL MCP | Running on `POSTGRES_MCP_HOST:POSTGRES_MCP_PORT` (default `localhost:5433`) |
| Google Calendar MCP | Running on `CALENDAR_MCP_HOST:CALENDAR_MCP_PORT` (default `localhost:5434`) |
| Focus agent LLM | `OPENROUTER_API_KEY` set, **or** `LOCAL_LLM_ENABLED=true` with a local OpenAI-compatible server at `LOCAL_LLM_BASE_URL` |

### Run tests

```bash
uv run ruff check backend
uv run mypy backend
uv run pytest
```

---

## 3. Frontend (Next.js)

In a second terminal:

```bash
cd frontend
npm ci
npm run dev
```

Open http://localhost:3000 — the dashboard calls the briefing API and shows the rendered briefing with an observability badge. A link to **Settings** (`/settings`) manages active consents (MVP 4+).

If the backend runs on a non-default host or port, create `frontend/.env.local`:

```bash
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
```

Default (when unset): `http://127.0.0.1:8000`.

Production-style build (standalone output):

```bash
npm run build
node .next/standalone/server.js
```

---

## 4. Full stack with Docker

From the repo root:

```bash
cp .env.example .env
docker compose up --build
```

| URL | Service |
|---|---|
| http://localhost | Nginx → Next.js UI |
| http://localhost/health | Backend health (proxied) |
| http://localhost/api/v1/briefing/generate | Briefing API (POST) |

If port **80** is already in use, change `docker-compose.yml`:

```yaml
ports:
  - "8080:80"
```

Then use http://localhost:8080.

Optional local Postgres for MCP testing:

```bash
docker compose --profile mcp up --build
```

---

## Epic E1 branch (MVP 1 scaffold)

Use this section when you want to run **Epic DB-E1** only — monorepo, Docker stack, FastAPI/Next.js scaffold, minimal LangGraph, and CI. It does **not** include core agents, MCP clients, or the briefing generation pipeline (those arrive in Epic E2).

### Checkout the branch

```bash
git fetch origin
git checkout epic/E1-project-scaffold
```

E1 is already merged into `epic/autonomus-implementation` (commit `4a578ef`). To run the same scaffold from the integration branch:

```bash
git checkout epic/autonomus-implementation
git pull origin epic/autonomus-implementation
```

To return to MVP 2 work later:

```bash
git checkout epic/E2-core-agents
```

### What E1 includes

| Feature | E1 (`epic/E1-project-scaffold`) | E2+ (current integration) |
|---|---|---|
| `GET /health` | Yes | Yes |
| Briefing API | `GET /api/v1/briefing/generate` → **501** placeholder | `POST /api/v1/briefing/generate` → full graph |
| LangGraph | `START → orchestrator → END` | Task, calendar, focus, critic, orchestrator |
| MCP / LLM agents | No | Yes |
| Prompt files | No | Yes |
| Backend tests | 8 tests | 15+ tests |

### E1 — environment setup

```bash
cp .env.example .env
uv sync --all-extras
```

E1 `.env.example` is smaller (no `OPENROUTER_BASE_URL`, MCP ports, or LLM model vars). Defaults are enough for health checks and scaffold tests.

### E1 — backend

```bash
uv run uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

Health check:

```bash
curl http://127.0.0.1:8000/health
```

Briefing placeholder (expects **501 Not Implemented**):

```bash
curl -i http://127.0.0.1:8000/api/v1/briefing/generate
```

You should see `HTTP/1.1 501 Not Implemented` and a JSON body with `"detail": "Briefing generation not yet implemented"`.

### E1 — frontend

```bash
cd frontend
npm ci
npm run dev
```

Open http://localhost:3000 — dashboard placeholder only.

### E1 — Docker full stack

```bash
cp .env.example .env
docker build -t daily-briefing:e1 .
docker compose up --build
```

Verify through Nginx:

```bash
curl http://localhost/health
curl -i http://localhost/api/v1/briefing/generate
```

### E1 — tests and CI parity

```bash
uv run ruff check backend
uv run mypy backend
uv run pytest
cd frontend && npm ci && npm run lint && npm run build
```

All jobs mirror `.github/workflows/ci.yml` on the E1 branch.

---

## 5. Troubleshooting

### `[Errno 13] Permission denied` on uvicorn

You likely used a privileged port (e.g. `--port 800`). Use `--port 8000`.

### `[Errno 48] Address already in use`

Another process is bound to the port:

```bash
lsof -nP -iTCP:8000 -sTCP:LISTEN
kill <PID>
```

Or run on another port: `--port 8001`.

### `Internal Server Error` on briefing generate (legacy)

Older builds returned **500** when MCP servers were unreachable. Current MVP 2 code returns **200 `degraded`** instead. If you still see 500:

1. Pull latest `epic/E2-core-agents` (or merged integration branch).
2. Restart uvicorn — see [After pulling code changes](#after-pulling-code-changes).
3. Check the uvicorn terminal for the stack trace (often `MCP transport error` or missing prompt files).

### Briefing returns degraded / empty content

- Confirm MCP servers are up at `POSTGRES_MCP_HOST:POSTGRES_MCP_PORT` and `CALENDAR_MCP_HOST:CALENDAR_MCP_PORT`.
- Set `OPENROUTER_API_KEY` for Focus agent planning, or enable `LOCAL_LLM_ENABLED` with a local OpenAI-compatible server.

### CORS errors from the browser

Ensure `CORS_ORIGINS` in `.env` includes your frontend origin (default includes `http://localhost:3000`).

### Briefing stuck on `awaiting_consent` (MVP 4+)

Grant calendar consent via the UI modal or `POST /api/v1/consent`, then generate again. Verify with:

```bash
curl "http://127.0.0.1:8000/api/v1/consent?user_id=user-1"
```

---

## Local notes (MVP 3+)

Epic **DB-E3** adds observability endpoints and a frontend dashboard. Use these when running `epic/E3-observability` or a branch that includes MVP 3.

### DLQ admin API

Set `ADMIN_API_KEY` in `.env` (see `.env.example`). Without it, DLQ routes return **503**.

```bash
# List failed agent events
curl http://127.0.0.1:8000/api/v1/dlq \
  -H "X-Admin-Key: dev-admin-key-change-in-production"

# Retry a failed event (security violations are rejected with 403)
curl -X POST http://127.0.0.1:8000/api/v1/dlq/{event_id}/retry \
  -H "X-Admin-Key: dev-admin-key-change-in-production"
```

Replace the header value with your `ADMIN_API_KEY`.

### Prometheus metrics

Scrape application metrics from:

```bash
curl http://127.0.0.1:8000/metrics/
```

Use the trailing slash — `/metrics` may redirect. No auth required.

Expected custom metrics include `briefing_generation_duration_seconds`, `agent_execution_duration_seconds`, `llm_tokens_used_total`, `mcp_call_duration_seconds`, `dlq_events_total`, and `security_violations_total`.

### Frontend → backend

The home page (`frontend/app/page.tsx`) POSTs to `/api/v1/briefing/generate` and renders the response in `BriefingDashboard` with `ObservabilityBadge`.

| Setup | Action |
|---|---|
| Backend on `127.0.0.1:8000` | No extra config — defaults work |
| Backend on another port | Set `NEXT_PUBLIC_API_BASE_URL` in `frontend/.env.local` |
| CORS errors in browser | Add frontend origin to `CORS_ORIGINS` in root `.env` |

Restart `npm run dev` after changing `frontend/.env.local`.

### OpenTelemetry (optional)

Tracing exports to `OTEL_EXPORTER_OTLP_ENDPOINT` when a collector is running. If the collector is down, the app logs a warning and continues without tracing.

---

## Try it locally (MVP 4+)

Epic **DB-E4** adds agentic consent, preferences learning, GDPR export, and local LLM routing for privacy-sensitive Focus agent calls. Use this flow on `epic/E4-agentic-consent` or any branch that includes MVP 4.

### End-to-end consent flow (UI)

1. Start backend and frontend (see [§2](#2-backend-fastapi--langgraph) and [§3](#3-frontend-nextjs)).
2. Open http://localhost:3000 and click **Generate briefing**.
3. Without Google Calendar consent, the API returns `"status": "awaiting_consent"` and a **ConsentPromptModal** appears.
4. Choose a TTL (e.g. **4 hours**) and click **Allow** — this calls `POST /api/v1/consent`.
5. Click **Generate briefing** again (or let the app retry after grant). With consent stored, the graph continues past the calendar agent.

Optional: set `GOOGLE_OAUTH_AUTHORIZE_URL` in `.env` to open Google OAuth in a popup when granting calendar access.

### Consent API (curl)

```bash
# Grant calendar consent for 4 hours
curl -X POST http://127.0.0.1:8000/api/v1/consent \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user-1",
    "service": "google_calendar",
    "scope": ["calendar.readonly"],
    "ttl_hours": 4
  }'

# List active consents
curl "http://127.0.0.1:8000/api/v1/consent?user_id=user-1"

# Revoke a consent (use id from list response)
curl -X DELETE http://127.0.0.1:8000/api/v1/consent/{consent_id}
```

After granting consent via curl, retry briefing generation:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/briefing/generate \
  -H "Content-Type: application/json" \
  -d '{"user_id":"user-1"}'
```

#### Expected `awaiting_consent` (no grant yet)

On MVP 4+, the calendar agent pauses the graph when consent is missing:

```json
{
  "status": "awaiting_consent",
  "briefing": "",
  "consent_request": {
    "request_id": "...",
    "service": "google_calendar",
    "scope": ["calendar.readonly"],
    "suggested_ttl_hours": 4,
    "agent_requesting": "calendar",
    "message": "Google Calendar consent required"
  },
  "metadata": { "...": "..." }
}
```

### Settings dashboard

Open http://localhost:3000/settings to:

- View active consents (service, scope, expiry, `times_used`)
- Revoke consent (with confirmation)
- Download data export (JSON link)

### Preferences feedback

Submit an edited briefing to learn user preferences for future Focus agent runs:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/preferences/feedback \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user-1",
    "briefing_id": "brief-001",
    "original_content": "Plan for the day",
    "edited_content": "Prefer morning deep work blocks"
  }'

curl "http://127.0.0.1:8000/api/v1/preferences?user_id=user-1"
```

### GDPR data export

```bash
# JSON (default)
curl "http://127.0.0.1:8000/api/v1/export?user_id=user-1&format=json" -o export.json

# CSV
curl "http://127.0.0.1:8000/api/v1/export?user_id=user-1&format=csv" -o export.csv
```

Rate limit: **5 requests per hour** per client IP.

### Local LLM for PII (optional)

When the Focus agent processes task/calendar context, data is classified as `confidential_pii` and routes to the local model if enabled:

```bash
LOCAL_LLM_ENABLED=true
LOCAL_LLM_BASE_URL=http://localhost:8080/v1
LOCAL_LLM_MODEL_ID=local/llama-3-8b
```

See [docs/LOCAL-LLM.md](../LOCAL-LLM.md) for server setup and fallback metrics.

---

## Quick reference

| Mode | Command | URL |
|---|---|---|
| Backend | `uv run uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000` | http://127.0.0.1:8000 |
| Metrics | `curl http://127.0.0.1:8000/metrics/` | http://127.0.0.1:8000/metrics/ |
| Frontend | `cd frontend && npm run dev` | http://localhost:3000 |
| Settings | — | http://localhost:3000/settings |
| Consent API | `curl http://127.0.0.1:8000/api/v1/consent?user_id=user-1` | — |
| Docker | `docker compose up --build` | http://localhost |

---

*See also: [README.md](../../README.md), [AGENT.md](../../AGENT.md), [docs/PLAN.md](../PLAN.md)*
