# Try It Locally — AI Daily Briefing Assistant

**Version:** 2.0 (Option 1 Enterprise Hybrid) | **Last Updated:** May 2026

This guide walks through running the project after the Option 1 setup: **Supabase**, **stdio MCP** (Postgres + Google Calendar via `npx`), and **Google OAuth**.

For Google Calendar credentials, complete [google-calandar-setup.md](./google-calandar-setup.md) first.

---

## Two ways to run

| Mode | Best for | URLs |
|---|---|---|
| **Local dev** | Day-to-day development | Backend **8010**, Frontend **3010** |
| **Docker** | Production-like smoke test | Nginx **80** (map to e.g. **8088** on host) |

With `MCP_TRANSPORT=stdio` (default), the backend **spawns MCP servers on demand** via `npx`. You do **not** need separate Postgres/Calendar MCP processes running on ports 5433/5434.

---

## What you're running

| Piece | Tech | Local dev URL | Inside Docker |
|---|---|---|---|
| Backend | FastAPI + LangGraph | http://127.0.0.1:8010 | nginx → :8000 |
| Frontend | Next.js 16 | http://localhost:3010 | nginx → :3000 |
| Postgres data | Supabase (pooler :6543) | via stdio MCP | via stdio MCP |
| Calendar | Google Calendar MCP (stdio) | via stdio MCP | via stdio MCP |
| Full stack | Docker + supervisord | — | http://localhost:8088 |

---

## Recommended first run

1. [Step 1](#step-1--install-prerequisites) — uv, Python 3.12, **Node 22**, optional Docker
2. [Step 2](#step-2--environment-setup) — configure `.env` (Supabase, OAuth, LLM)
3. [Step 3](#step-3--database-migration) — `alembic upgrade head` against Supabase
4. [Step 4](#step-4--google-calendar-oauth) — verify token exchange (200)
5. [Step 5](#step-5--backend-fastapi--langgraph) — start API on **8010**, `curl /health`
6. [Step 6](#step-6--frontend-nextjs) — `npm run dev` on **3010**
7. [Step 7](#step-7--generate-a-briefing) — POST briefing or use the UI
8. Optional: [Step 8](#step-8--full-stack-with-docker) — Docker smoke test

---

## Step 1 — Install prerequisites

| Tool | Required | Notes |
|---|---|---|
| [uv](https://docs.astral.sh/uv/) | Yes | Python dependency manager |
| Python 3.12+ | Yes | Installed via `uv sync` |
| Node.js **22.x** | Yes for calendar MCP | `.nvmrc` → `22`; calendar MCP fails on Node 20 |
| Docker 27+ | Optional | Full-stack container |

Verify from repo root:

```bash
cd /path/to/daily-briefing

uv --version
uv run python --version
node --version    # expect v22.x
test -f .env && echo ".env OK" || echo "Run: cp .env.example .env"
```

### Install Node.js 22

```bash
nvm install 22
nvm use
node --version
```

Without nvm: install from https://nodejs.org/ (22.x LTS).

---

## Step 2 — Environment setup

```bash
cp .env.example .env   # skip if .env exists; merge any new keys
```

Edit `.env`. Required for a **full briefing**:

| Variable | Purpose |
|---|---|
| `DATABASE_URL` | Supabase async URL (`postgresql+asyncpg://…:6543/postgres?sslmode=require`) |
| `MCP_POSTGRES_URL` | Same DB, sync driver URL (`postgresql://…`) for Postgres MCP |
| `MCP_TRANSPORT` | `stdio` (Option 1 default) |
| `GOOGLE_CLIENT_ID` | Web application OAuth client (see calendar setup guide) |
| `GOOGLE_CLIENT_SECRET` | Same client as above |
| `GOOGLE_REFRESH_TOKEN` | Issued from OAuth Playground — **must match same client** |
| `OPENROUTER_API_KEY` | Focus agent LLM calls |

Local dev port overrides (preserve these if you use non-default ports):

```env
# default: 5433 — only used when MCP_TRANSPORT=http
POSTGRES_MCP_PORT=5443
# default: 5434 — only used when MCP_TRANSPORT=http
CALENDAR_MCP_PORT=5444
# default: 4317
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4347
# default: 3000 — browser CORS for local Next.js
CORS_ORIGINS=http://localhost:3010,http://127.0.0.1:3010,http://localhost
```

**Frontend API URL** is resolved automatically — see [Frontend API URL (automatic)](#frontend-api-url-automatic). You do **not** need to edit `frontend/.env.local` when switching between Docker and local backend.

**`.env` rules:**

- URL-encode `$` in passwords as `%24`
- Do **not** quote `DATABASE_URL` values
- Put comments on the line **above** a value — inline `#` comments break Docker `--env-file`

---

## Step 3 — Database migration

Run Alembic once against your Supabase project:

```bash
uv sync --all-extras
uv run alembic upgrade head
```

Expected: migration `001_initial_schema` creates `tasks`, `dlq_events`, `user_preferences`, `consent_*` tables.

### Seed a test task (optional)

The UI defaults to `user_id=user-1`. Insert at least one pending task in Supabase SQL editor:

```sql
INSERT INTO tasks (id, user_id, title, priority, due_date, status, created_at)
VALUES (
  gen_random_uuid(),
  'user-1',
  'Review daily briefing setup',
  'high',
  CURRENT_DATE,
  'pending',
  NOW()
);
```

Integration tests use `demo-user` — seed similarly if you run `LIVE_STDIO_E2E=1` tests.

---

## Step 4 — Google Calendar OAuth

Follow [google-calandar-setup.md](./google-calandar-setup.md) end-to-end, then verify:

```bash
uv run python -c "
import httpx
from backend.settings import get_settings
get_settings.cache_clear()
s = get_settings()
r = httpx.post('https://oauth2.googleapis.com/token', data={
    'client_id': s.google_client_id,
    'client_secret': s.google_client_secret,
    'refresh_token': s.google_refresh_token,
    'grant_type': 'refresh_token',
})
print(r.status_code)
print(r.text[:300])
"
```

Expected: **200** with an `access_token`. If you get `401 unauthorized_client`, all three OAuth values must come from the **same** Web application client.

---

## Step 5 — Backend (FastAPI + LangGraph)

Terminal 1 — from repo root:

```bash
uv sync --all-extras
uv run uvicorn backend.main:app --reload \
  --reload-dir backend --reload-dir prompts \
  --host 127.0.0.1 --port 8010
```

Use **`8010`** for local dev (not `8000`, which Docker uses internally).

**Important:** Limit `--reload-dir` to `backend` and `prompts` only. Watching `frontend/node_modules` triggers reload loops and **503** responses. See [503 — Server shutting down](#503--server-shutting-down).

### Health check

```bash
curl http://127.0.0.1:8010/health
```

Expected:

```json
{"status":"healthy","version":"0.1.0"}
```

---

## Step 6 — Frontend (Next.js)

Terminal 2:

```bash
cd frontend
npm ci
npm run dev
```

Open http://localhost:3010 — the dashboard auto-detects the backend at **8010** (see below).

### Frontend API URL (automatic)

`frontend/lib/api.ts` picks the backend URL at runtime in the browser:

| You open | API calls go to |
|---|---|
| http://localhost:8088 (Docker) | Same origin → `http://localhost:8088/api/...` |
| http://localhost:3010 (local dev) | `http://127.0.0.1:8010/api/...` |

No `frontend/.env.local` changes needed when switching modes.

**Optional override** — only for hybrid setups (local Next.js on 3010 → Docker API on 8088):

```env
# frontend/.env.local
NEXT_PUBLIC_API_BASE_URL=http://localhost:8088
```

Restart `npm run dev` after changing `frontend/.env.local`.

Production-style build:

```bash
npm run build
node .next/standalone/server.js
```

---

## Step 7 — Generate a briefing

### Via curl

```bash
curl -X POST http://127.0.0.1:8010/api/v1/briefing/generate \
  -H "Content-Type: application/json" \
  -d '{"user_id":"user-1"}'
```

Response includes `X-Trace-Id` header.

### Via UI

1. Open http://localhost:3010
2. Click **Generate briefing**
3. If calendar consent is required, grant via the modal (MVP 4+) or see [Consent API](#consent-api-curl) below
4. Expect `"status": "success"` or `"degraded"` depending on agent outcomes

### Expected without full setup

If Supabase, OAuth, or OpenRouter are missing, **200** with `"status": "degraded"` is normal — agents fail gracefully.

### Live stdio integration tests (optional)

```bash
LIVE_STDIO_E2E=1 uv run pytest backend/tests/integration/test_live_stdio_briefing.py -q
```

Expect **2 passed** (Postgres query + task agent against Supabase).

---

## Step 8 — Full stack with Docker

For the complete Docker guide (prerequisites, `.env`, LLM, troubleshooting), see [docker-setup.md](./docker-setup.md).

Build and run the production container (nginx + FastAPI + Next.js + supervisord MCP programs):

```bash
docker build -t briefing:latest .
docker rm -f briefing-smoke 2>/dev/null
docker run -d --name briefing-smoke \
  --env-file .env \
  -e CORS_ORIGINS=http://localhost \
  -p 8088:80 \
  briefing:latest
```

| URL | Service |
|---|---|
| http://localhost:8088 | Next.js UI (via nginx) |
| http://localhost:8088/health | Backend health |
| http://localhost:8088/api/v1/briefing/generate | Briefing API (POST) |

**Why `-e CORS_ORIGINS=http://localhost`?** Your `.env` lists port **3010** origins for local dev. The browser hits port **8088** in Docker — override CORS at run time.

Check calendar MCP is healthy (no crash loop):

```bash
docker logs briefing-smoke 2>&1 | grep -i calendar
```

Stop the container:

```bash
docker rm -f briefing-smoke
```

### Docker Compose — build and run

From repo root (`.env` must exist with Supabase + Google OAuth + OpenRouter):

```bash
# Build image + start container (foreground — logs in terminal)
docker compose up --build

# Same, detached (background)
docker compose up --build -d

# Force full rebuild (no cache)
docker compose build --no-cache
docker compose up -d

# Follow logs
docker compose logs -f app

# Stop and remove container
docker compose down
```

Default mapping: **http://localhost:8088** → nginx → FastAPI (:8000) + Next.js (:3000) inside the container.

| URL | What it is |
|---|---|
| http://localhost:8088 | Dashboard UI |
| http://localhost:8088/settings | Consent / export settings |
| http://localhost:8088/health | Backend health |
| http://localhost:8088/api/v1/briefing/generate | Briefing API (POST) |

Verify:

```bash
curl http://localhost:8088/health
docker compose logs app 2>&1 | grep -i calendar   # no credential errors
```

The UI inside Docker uses the same automatic detection (browser on `:8088` → same-origin API). **No `frontend/.env.local` change or rebuild** required when switching from local dev to Docker.

---

## Using Docker alongside local frontend/backend

You can mix **Docker** (full production stack) with **local dev** (hot reload). Pick one primary UI path:

### Mode A — Everything in Docker (simplest)

1. `docker compose up --build -d`
2. Open http://localhost:8088 → **Generate briefing**

No local uvicorn or `npm run dev` needed.

### Mode B — Local frontend + Docker backend (hybrid)

Use Docker for API + MCP; run Next.js locally with hot reload.

| Process | Where | URL |
|---|---|---|
| Backend + MCP + nginx | Docker | http://localhost:8088 |
| Frontend dev server | Local terminal | http://localhost:3010 |

1. Start Docker:

   ```bash
   docker compose up --build -d
   curl http://localhost:8088/health
   ```

2. Optional — only if auto-detection is not enough, set override in `frontend/.env.local`:

   ```env
   NEXT_PUBLIC_API_BASE_URL=http://localhost:8088
   ```

3. Terminal — local frontend only:

   ```bash
   cd frontend && npm run dev
   ```

4. Open http://localhost:3010

   Auto-detection uses **8010** when the UI is on port 3010. For Mode B you **must** set the override in step 2 so API calls go to Docker on **8088**.

`docker-compose.yml` sets CORS for both `:8088` and `:3010`.

### Mode C — Local frontend + local backend (daily development)

Use when editing Python/React with `--reload` / hot reload. **Stop Docker app** if running: `docker compose down`

1. Terminal 1 — backend:

   ```bash
   uv run uvicorn backend.main:app --reload \
     --reload-dir backend --reload-dir prompts \
     --host 127.0.0.1 --port 8010
   ```

2. Terminal 2 — frontend (no `.env.local` needed):

   ```bash
   cd frontend && npm run dev
   ```

3. Open http://localhost:3010 — API auto-detects **8010**

### Mode D — Local backend + Docker only for optional Postgres

For legacy HTTP MCP testing (`MCP_TRANSPORT=http`), not needed with stdio + Supabase:

```bash
docker compose --profile mcp up postgres -d
```

---

## Step 9 — Run tests (optional)

```bash
uv run ruff check backend
uv run mypy backend
uv run pytest
```

90 unit tests should pass. Live integration tests require `LIVE_STDIO_E2E=1` and Supabase configured.

---

## Troubleshooting

### Node.js version mismatch

Calendar MCP requires **Node 22**. If `node --version` shows v20:

```bash
nvm install 22 && nvm use
```

Use Docker for calendar MCP if you cannot upgrade Node locally.

### `[Errno 48] Address already in use`

```bash
lsof -nP -iTCP:8010 -sTCP:LISTEN
kill <PID>
# or force:
lsof -ti :8010 | xargs kill -9
```

Same for port **3010** if Next.js fails to start.

### Calendar MCP credential errors

| Symptom | Fix |
|---|---|
| `Failed to validate Google Calendar credentials` | Re-run [Step 4](#step-4--google-calendar-oauth) token verify script |
| `401 unauthorized_client` | Client ID/secret/token mismatch — re-issue all three from same Web client |
| `redirect_uri_mismatch` in Playground | Use **Web application** client with `https://developers.google.com/oauthplayground` redirect URI |
| `403 access_denied` | Add your Gmail as **Test user** on OAuth consent screen |

See [google-calandar-setup.md](./google-calandar-setup.md).

### Supabase / DATABASE_URL errors

| Symptom | Fix |
|---|---|
| `sslmode` / asyncpg errors | Use `postgresql+asyncpg://` for `DATABASE_URL`; `%24` for `$` in password |
| Prepared statement errors (Supavisor) | Already handled via `statement_cache_size=0` in `backend/db/session.py` |
| Empty tasks | Seed rows for `user-1` in Supabase (see [Step 3](#step-3--database-migration)) |

### CORS errors from the browser

Ensure `CORS_ORIGINS` includes the **exact** origin you open:

```env
CORS_ORIGINS=http://localhost:3010,http://127.0.0.1:3010,http://localhost
```

Restart uvicorn after changing root `.env`. Restart `npm run dev` after changing `frontend/.env.local`.

### 503 — Server shutting down {#503--server-shutting-down}

Caused by uvicorn `--reload` watching `frontend/node_modules`. Fix:

1. Stop uvicorn (Ctrl+C); `lsof -ti :8010 | xargs kill -9` if stuck
2. Restart with `--reload-dir backend --reload-dir prompts` only
3. Confirm: `curl -s http://127.0.0.1:8010/health` → **200**

### Briefing stuck on `awaiting_consent`

Grant calendar consent via the UI modal or:

```bash
curl -X POST http://127.0.0.1:8010/api/v1/consent \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user-1",
    "service": "google_calendar",
    "scope": ["calendar.readonly"],
    "ttl_hours": 4
  }'
```

Then retry briefing generation.

### Docker: UI loads but API calls fail

Check browser devtools → Network. API base should match your mode (`8088` same-origin or `8010` local). For hybrid Mode B, set `NEXT_PUBLIC_API_BASE_URL=http://localhost:8088` in `frontend/.env.local`.

Or test API directly via curl on `/health` and `/api/v1/briefing/generate`.

---

## Local notes (MVP 3+)

### DLQ admin API

Set `ADMIN_API_KEY` in `.env`. Without it, DLQ routes return **503**.

```bash
curl http://127.0.0.1:8010/api/v1/dlq \
  -H "X-Admin-Key: dev-admin-key-change-in-production"
```

### Prometheus metrics

```bash
curl http://127.0.0.1:8010/metrics/
```

**Full observability stack (Prometheus + Grafana + PagerDuty):** See [docs/guidence/observability/README.md](../guidence/observability/README.md). Required before Week 1 gap remediation kickoff.

### OpenTelemetry (optional)

Tracing exports to `OTEL_EXPORTER_OTLP_ENDPOINT` (default `4317`; local override e.g. `4347`). App continues if collector is down.

---

## Try it locally (MVP 4+)

### End-to-end consent flow (UI)

1. Start backend ([Step 5](#step-5--backend-fastapi--langgraph)) and frontend ([Step 6](#step-6--frontend-nextjs))
2. Open http://localhost:3010 → **Generate briefing**
3. Without calendar consent → `"status": "awaiting_consent"` and consent modal
4. Grant consent → generate again

### Consent API (curl)

```bash
curl -X POST http://127.0.0.1:8010/api/v1/consent \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user-1",
    "service": "google_calendar",
    "scope": ["calendar.readonly"],
    "ttl_hours": 4
  }'

curl "http://127.0.0.1:8010/api/v1/consent?user_id=user-1"
```

### Settings dashboard

http://localhost:3010/settings — view/revoke consents, export data.

### Local LLM for PII (optional)

```bash
LOCAL_LLM_ENABLED=true
LOCAL_LLM_BASE_URL=http://localhost:8080/v1
```

See [docs/LOCAL-LLM.md](../LOCAL-LLM.md).

---

## Epic E1 branch (MVP 1 scaffold — legacy)

Use only when running **Epic DB-E1** scaffold without agents/MCP. Current Option 1 setup uses the steps above.

```bash
git fetch origin
git checkout epic/E1-project-scaffold
```

E1 uses port **8010** for local uvicorn but briefing API returns **501 Not Implemented**. See git history for E1-specific docs if needed.

---

## Quick reference

| Step | Mode | Command | URL |
|---|---|---|---|
| 1 | Prerequisites | `uv --version && node --version` | — |
| 3 | DB migrate | `uv run alembic upgrade head` | — |
| 4 | OAuth verify | See [Step 4](#step-4--google-calendar-oauth) | — |
| 5 | Backend | `uv run uvicorn backend.main:app --reload --reload-dir backend --reload-dir prompts --host 127.0.0.1 --port 8010` | http://127.0.0.1:8010 |
| 6 | Frontend | `cd frontend && npm ci && npm run dev` | http://localhost:3010 |
| 7 | Briefing | `curl -X POST http://127.0.0.1:8010/api/v1/briefing/generate -H "Content-Type: application/json" -d '{"user_id":"user-1"}'` | — |
| 8 | Docker | `docker compose up --build -d` | http://localhost:8088 |
| 9 | Tests | `uv run pytest` | — |

---

*See also: [README.md](../../README.md), [docker-setup.md](./docker-setup.md), [google-calandar-setup.md](./google-calandar-setup.md), [docs/LOCAL-LLM.md](../LOCAL-LLM.md)*
