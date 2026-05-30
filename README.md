# AI Daily Briefing Assistant

Multi-agent orchestration system for personalized daily briefings. Built with LangGraph, FastAPI, and Next.js, deployed as a single Docker container with Nginx and Supervisord.

## Architecture

- **Backend:** FastAPI + LangGraph agent orchestration
- **Frontend:** Next.js 16 (App Router, standalone output)
- **Deployment:** Single container — Nginx → Next.js (3000) + FastAPI (8000)
- **Integrations:** PostgreSQL MCP, Google Calendar MCP (MVP 2+)

## Prerequisites

- [uv](https://docs.astral.sh/uv/) >= 0.5
- Node.js 22.x (`nvm use` reads `.nvmrc`)
- Docker 27+

## Quick Start (Local Development)

### Backend

```bash
cp .env.example .env
uv sync --all-extras
uv run uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

Health check: `curl http://localhost:8000/health`

### Frontend

```bash
cd frontend
npm ci
npm run dev
```

Open http://localhost:3000

### Docker (full stack)

```bash
cp .env.example .env
docker compose up --build
```

Open http://localhost — API at `/api/v1/`, health at `/health`.

> **Note:** Port 80 may be in use locally. Change `ports` in `docker-compose.yml` to `"8080:80"` and use http://localhost:8080.

## Project Structure

```
backend/          FastAPI app, LangGraph, schemas
frontend/         Next.js dashboard
docs/             Architecture, epics, execution rules
prompts/          Agent prompt contracts (MVP 2+)
```

## Workflow

See [AGENT.md](./AGENT.md) for development workflow and [docs/PLAN.md](./docs/PLAN.md) for implementation progress.

## Production Deployment

1. Copy [`.env.production.example`](./.env.production.example) and configure secrets.
2. Pull a **Cosign-signed** image from GHCR (see [infrastructure/DEPLOYMENT.md](./infrastructure/DEPLOYMENT.md)).
3. Verify probes:
   - Liveness: `GET /health`
   - Readiness: `GET /health/ready`
4. Load Prometheus rules from `infrastructure/monitoring/` and alerts from `infrastructure/alerting/rules.yml`.

Full guide: [infrastructure/DEPLOYMENT.md](./infrastructure/DEPLOYMENT.md)

## License

Private — internal use.
