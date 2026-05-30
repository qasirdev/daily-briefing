# Try It Locally — AI Daily Briefing Assistant

**Version:** 1.1.0 | **Last Updated:** May 2026

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

```bash
curl -X POST http://127.0.0.1:8000/api/v1/briefing/generate \
  -H "Content-Type: application/json" \
  -d '{"user_id":"user-1"}'
```

Response includes `X-Trace-Id` in headers. For live task/calendar data, PostgreSQL and Google Calendar MCP servers must be running on the ports in `.env`. Without them, the graph may return a degraded or empty briefing depending on agent errors.

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

Open http://localhost:3000 for the dashboard placeholder.

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

### Briefing returns degraded / empty content

- Confirm MCP servers are up at `POSTGRES_MCP_HOST:POSTGRES_MCP_PORT` and `CALENDAR_MCP_HOST:CALENDAR_MCP_PORT`.
- Set `OPENROUTER_API_KEY` for Focus agent planning, or enable `LOCAL_LLM_ENABLED` with a local OpenAI-compatible server.

### CORS errors from the browser

Ensure `CORS_ORIGINS` in `.env` includes your frontend origin (default includes `http://localhost:3000`).

---

## Quick reference

| Mode | Command | URL |
|---|---|---|
| Backend | `uv run uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000` | http://127.0.0.1:8000 |
| Frontend | `cd frontend && npm run dev` | http://localhost:3000 |
| Docker | `docker compose up --build` | http://localhost |

---

*See also: [README.md](../../README.md), [AGENT.md](../../AGENT.md), [docs/PLAN.md](../PLAN.md)*
