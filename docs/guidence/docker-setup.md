# Docker Setup — AI Daily Briefing Assistant

**Version:** 1.0 (Option 1 Enterprise Hybrid) | **Last Updated:** May 2026

This guide covers running the **full production stack** in Docker: nginx, FastAPI, Next.js, Postgres MCP (stdio), and Google Calendar MCP (stdio) — all managed by supervisord in a single container.

For local dev without Docker (ports 8010/3010), see [try-it-locally.md](./try-it-locally.md).

---

## What runs in the container

| Process | Internal port | Role |
|---|---|---|
| nginx | 80 | Reverse proxy — UI + `/api/*` |
| FastAPI + LangGraph | 8000 | Briefing API |
| Next.js (standalone) | 3000 | Dashboard UI |
| mcp-postgres | stdio | Supabase via `npx` |
| mcp-google-calendar | stdio | Google Calendar via `npx` |

Host mapping: **http://localhost:8088** → nginx:80

```
Browser :8088
    └── nginx :80
            ├── /        → Next.js :3000
            ├── /api/*   → FastAPI :8000
            └── /health  → FastAPI :8000
```

MCP servers are spawned on demand by the backend (`MCP_TRANSPORT=stdio`). You do **not** need separate MCP containers for Option 1.

---

## Prerequisites

| Requirement | Notes |
|---|---|
| Docker 27+ | [Install Docker](https://docs.docker.com/get-docker/) |
| `.env` configured | Supabase, Google OAuth, OpenRouter — see below |
| Supabase schema | Run `alembic upgrade head` once before first briefing |
| Google Calendar OAuth | [google-calandar-setup.md](./google-calandar-setup.md) |
| Supabase tasks seeded | At least one row for `user_id=user-1` (optional but recommended) |

---

## Step 1 — Configure `.env`

```bash
cp .env.example .env
```

### Required variables

| Variable | Purpose |
|---|---|
| `DATABASE_URL` | Supabase async URL (`postgresql+asyncpg://…:6543/postgres?sslmode=require`) |
| `MCP_POSTGRES_URL` | Same DB, sync URL (`postgresql://…`) for Postgres MCP |
| `MCP_TRANSPORT` | `stdio` |
| `GOOGLE_CLIENT_ID` | Web application OAuth client |
| `GOOGLE_CLIENT_SECRET` | Same client as above |
| `GOOGLE_REFRESH_TOKEN` | From OAuth Playground — **must match same client** |
| `OPENROUTER_API_KEY` | Focus agent LLM |
| `LLM_PRIMARY_MODEL` | e.g. `openai/gpt-4o-mini` or `openai/gpt-oss-120b` |

### Docker-specific settings

```env
GOOGLE_OAUTH_REDIRECT_URI=http://localhost:8088
MCP_TRANSPORT=stdio

# LLM — recommended for Docker (OpenRouter with PII masking)
LOCAL_LLM_ENABLED=false

# If using a local LLM on the host machine instead:
# LOCAL_LLM_ENABLED=true
# LOCAL_LLM_BASE_URL=http://host.docker.internal:8080/v1
```

### `.env` rules (important)

- URL-encode `$` in passwords as `%24`
- Do **not** quote `DATABASE_URL` values
- Put comments on the line **above** a value — inline `#` comments break Docker `--env-file`

`docker-compose.yml` overrides `CORS_ORIGINS` for ports **8088** and **3010**, so local-dev CORS values in `.env` do not block the Docker UI.

---

## Step 2 — Database migration (once)

Run against Supabase **before** the first briefing:

```bash
uv sync --all-extras
uv run alembic upgrade head
```

Seed a test task (Supabase SQL editor):

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

---

## Step 3 — Google OAuth redirect URIs

On your **Web application** OAuth client in Google Cloud, add:

```
https://developers.google.com/oauthplayground
http://localhost:8088
http://localhost:3010
```

See [google-calandar-setup.md](./google-calandar-setup.md) for the full OAuth flow.

Verify token exchange from the host:

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
print(r.status_code, r.text[:200])
"
```

Expected: **200** with an `access_token`.

---

## Step 4 — Build and run

From the repo root:

### Local (fast — default)

Skips **torch / LlamaFirewall** (~1 GB). Regex + constitutional injection layers remain active; set `LLAMAFIREWALL_ENABLED=false` in `.env` (default in `.env.example`).

```bash
docker compose build app && docker compose up -d

# Build image + start (foreground — logs in terminal)
docker compose up --build app

# Build + start in background
docker compose up --build -d app

# Force full rebuild (after Dockerfile or code changes)
docker compose build --no-cache app
docker compose up -d app

# Follow logs
docker compose logs -f app

# Stop and remove
docker compose down
```

### Production / PromptGuard testing (`promptguard` profile)

Installs **LlamaFirewall + transformers + torch**. First build is slow (~10–15 min). Set `LLAMAFIREWALL_ENABLED=true` and `HF_TOKEN` in `.env` for runtime ML scanning.

```bash
# Stop the fast local container if it is using port 8088
docker compose down

# Build with ML stack; HF_TOKEN preloads the model into the image when set
export HF_TOKEN=hf_xxx   # optional but recommended for production
docker compose --profile promptguard build app-promptguard
docker compose --profile promptguard up -d app-promptguard

docker compose --profile promptguard logs -f app-promptguard
```

CI/GHCR images are built with `INSTALL_PROMPTGUARD=true` automatically (see `.github/workflows/docker-publish.yml`).

---

## Step 5 — Verify

```bash
# Health
curl http://localhost:8088/health
# → {"status":"healthy","version":"0.1.0"}

# Calendar MCP (no credential crash loop)
docker compose logs app 2>&1 | grep -i calendar
# → should see "Calendar MCP Server started", NOT repeated credential errors

# Prompts present in image
docker compose exec app ls /app/prompts/focus/system.md

# Briefing
curl -X POST http://localhost:8088/api/v1/briefing/generate \
  -H "Content-Type: application/json" \
  -d '{"user_id":"user-1"}'
```

### Expected success response

| Field | Expected |
|---|---|
| `status` | `"success"` |
| `metadata.agents_invoked` | task, calendar, focus, critic, orchestrator |
| `metadata.total_tokens` | > 0 |
| `metadata.model_used` | your `LLM_PRIMARY_MODEL` |
| focus agent | `status: "success"`, tokens > 0 |

Open **http://localhost:8088** → **Generate briefing**.

---

## Using the app

| URL | Purpose |
|---|---|
| http://localhost:8088 | Dashboard |
| http://localhost:8088/settings | Consent management |
| http://localhost:8088/health | Backend health |
| http://localhost:8088/api/v1/briefing/generate | Briefing API (POST) |

### Frontend API URL (automatic)

The UI detects Docker automatically — when opened on port **8088**, API calls use the same origin (`http://localhost:8088/api/...`). No `frontend/.env.local` changes needed for all-in-Docker mode.

### Consent flow

1. Click **Generate briefing**
2. If prompted, grant Google Calendar consent via the modal
3. An OAuth popup may open (optional UX) — calendar access uses `GOOGLE_REFRESH_TOKEN` in `.env`
4. If the browser lands on `http://localhost:8088/?code=...&scope=...` after OAuth, that is normal; navigate to `http://localhost:8088/` — the auth code is not used by the app

---

## LLM configuration in Docker

The Focus agent sends task + calendar data as `confidential_pii`.

| Setup | `.env` | Behaviour |
|---|---|---|
| **OpenRouter only** (recommended) | `LOCAL_LLM_ENABLED=false` | Masked OpenRouter calls |
| **Local LLM on host** | `LOCAL_LLM_ENABLED=true`<br>`LOCAL_LLM_BASE_URL=http://host.docker.internal:8080/v1` | PII routed to host LLM; falls back to masked OpenRouter if unreachable |

**Do not use** `LOCAL_LLM_BASE_URL=http://localhost:8080/v1` in Docker — `localhost` inside the container is not your Mac. That causes Focus to escalate and the briefing to show `degraded`.

`docker-compose.yml` includes `host.docker.internal:host-gateway` for reaching a host-side LLM.

---

## Hybrid development

You can run Docker for the backend while developing the frontend locally:

| Process | Where | URL |
|---|---|---|
| Full stack | Docker | http://localhost:8088 |
| Next.js dev only | Local | http://localhost:3010 |

For hybrid (local UI → Docker API), set in `frontend/.env.local`:

```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8088
```

See [try-it-locally.md — Using Docker alongside local frontend/backend](./try-it-locally.md#using-docker-alongside-local-frontendbackend).

---

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `Prompt file not found: /app/prompts/...` | `prompts/` not in image | Rebuild: `docker compose up --build` (Dockerfile copies `prompts/`) |
| `501 OAuth not configured` | Missing Google client credentials | Set `GOOGLE_CLIENT_ID` / `SECRET` / `REFRESH_TOKEN`; OAuth URL is auto-built |
| Calendar MCP crash loop | Invalid OAuth token or client mismatch | Re-issue all three from same Web client — [google-calandar-setup.md](./google-calandar-setup.md) |
| Focus **escalated**, 0 tokens | Local LLM unreachable in container | Set `LOCAL_LLM_ENABLED=false` or use `host.docker.internal:8080` |
| `status: degraded`, calendar only | Focus failed (LLM) | Check `OPENROUTER_API_KEY`; verify with curl test above |
| CORS errors in browser | Wrong origin | `docker-compose.yml` sets CORS for 8088/3010; restart container |
| OTEL `localhost:4347` warnings | No collector in container | Harmless — set `OTEL_EXPORTER_OTLP_ENDPOINT` to a reachable host or ignore |
| Briefing slow (~30–60s) | Cold MCP spawns + LLM | Normal for first request; MCP and LLM warm up on subsequent runs |
| Port 8088 in use | Another process | Change `docker-compose.yml` to `"8090:80"` and use http://localhost:8090 |
| Docker Desktop stuck on **Starting...** | Docker VM / daemon not running | See [Docker Desktop stuck (macOS)](#docker-desktop-stuck-on-starting-macos) below |

### Docker Desktop stuck on "Starting..." (macOS)

If Docker Desktop on your Mac is stuck on **Starting...**, try these steps **in order**.

#### Quick fix (solves most cases)

```bash
pkill -9 Docker
pkill -9 com.docker.backend
pkill -9 vpnkit
pkill -9 dockerd
pkill -9 containerd
open -a Docker
```

Wait until Docker Desktop shows **Running**, then retry:

```bash
docker compose up -d --build --force-recreate
```

#### 1. Force quit Docker Desktop

```bash
pkill -f Docker
```

Or:

```bash
killall Docker
```

#### 2. Kill Docker background processes

```bash
pkill -9 com.docker.backend
pkill -9 vpnkit
pkill -9 dockerd
pkill -9 containerd
```

Verify nothing is left:

```bash
ps aux | grep -i docker
```

#### 3. Start Docker Desktop from Terminal

Intel and Apple Silicon:

```bash
open -a Docker
```

Or:

```bash
open /Applications/Docker.app
```

#### 4. Check Docker logs

If it still hangs:

```bash
tail -f ~/Library/Containers/com.docker.docker/Data/log/vm/*.log
```

Or:

```bash
tail -100 ~/Library/Group\ Containers/group.com.docker/logs/*
```

#### 5. Reset Docker Desktop (without deleting images)

Remove cached state:

```bash
rm -rf ~/Library/Group\ Containers/group.com.docker/settings-store.json
```

Then restart Docker Desktop:

```bash
open -a Docker
```

#### 6. Restart Docker VM services

```bash
launchctl stop com.docker.helper
launchctl start com.docker.helper
open -a Docker
```

#### 7. Check virtualization support

```bash
sysctl kern.hv_support
```

Expected:

```text
kern.hv_support: 1
```

#### 8. Complete cleanup (last resort)

This removes Docker Desktop settings and **may remove containers/images**. Reinstall the latest [Docker Desktop](https://docs.docker.com/desktop/setup/install/mac-install/) afterward.

```bash
rm -rf ~/Library/Containers/com.docker.docker
rm -rf ~/Library/Group\ Containers/group.com.docker
```

#### Still stuck?

Collect diagnostics before reinstalling or asking for help:

```bash
sw_vers
uname -m
docker version
ps aux | grep -i docker
```

Note your **macOS version**, **Intel vs Apple Silicon (M1/M2/M3/M4)**, and **Docker Desktop version** (Docker menu → **About Docker Desktop**).

### Useful debug commands

```bash
# All recent logs
docker compose logs app --tail 100

# LLM retries / errors
docker compose logs app 2>&1 | grep -iE 'llm|openrouter|chat/completions|focus'
docker compose logs app | grep llm_generation_complete

# Environment inside container (redact secrets before sharing)
docker compose exec app printenv MCP_TRANSPORT OPENROUTER_API_KEY LLM_OPENROUTER_MODELS LLM_PRIMARY_MODEL LOCAL_LLM_ENABLED LOCAL_LLM_BASE_URL

# OAuth endpoint
curl http://localhost:8088/api/v1/consent/oauth/google_calendar
```

---

## Optional: local Postgres (legacy HTTP MCP)

Only needed if `MCP_TRANSPORT=http` (not used with Option 1 + Supabase):

```bash
docker compose --profile mcp up postgres -d
```

---

## Quick reference

```bash
# First-time setup
cp .env.example .env          # edit secrets
uv run alembic upgrade head   # Supabase schema

# Run
docker compose up --build -d

# Verify
curl http://localhost:8088/health
open http://localhost:8088

# Rebuild after code changes
docker compose up --build -d

# Stop
docker compose down
```

---

*See also: [try-it-locally.md](./try-it-locally.md), [google-calandar-setup.md](./google-calandar-setup.md), [supabase-setup.md](./supabase-setup.md)*
