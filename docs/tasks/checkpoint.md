# Session Checkpoint — Option 1 Enterprise Hybrid — May 2026

## Current State
- **Phase:** 3 (Option 1 implementation) — substantially complete
- **Branch:** uncommitted working tree on epic/E6-production (or current branch)

## Completed This Session
- [x] Supabase async SQLAlchemy + Alembic (`backend/db/`, `alembic.ini`, migration `001_initial_schema`)
- [x] Stdio MCP transport (`backend/mcp/stdio_transport.py`, `postgres_stdio.py`, `calendar_stdio.py`)
- [x] `MCP_TRANSPORT=stdio` in settings; HTTP MCP clients unchanged for unit tests
- [x] DLQ persistence via SQLAlchemy (Supavisor-safe `statement_cache_size=0`)
- [x] Supervisord: mcp-postgres, mcp-google-calendar, nginx port fix (8000/3000)
- [x] Dockerfile: Node.js 22, alembic.ini copy
- [x] `.env.example` / `.env.production.example` updated
- [x] Jira epic DB-E7 (DB-053–DB-057)
- [x] 90 unit tests passing + 2 live stdio integration tests (with `LIVE_STDIO_E2E=1`)
- [x] Docker smoke test: `/health` returns 200 via port 8088→80

## Local dev port map (preserve in `.env`)

| Variable | Your value | Default | Used when |
|---|---|---|---|
| `POSTGRES_MCP_PORT` | **5443** | 5433 | `MCP_TRANSPORT=http` only |
| `CALENDAR_MCP_PORT` | **5444** | 5434 | `MCP_TRANSPORT=http` only |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | **4347** | 4317 | Readiness probe |
| `NEXT_PUBLIC_API_BASE_URL` | **8010** | 8000 | Next.js → FastAPI (local, no nginx) |
| `CORS_ORIGINS` | **3010** origins | 3000 | Browser CORS for local Next.js |

**Important:** Inline comments on the same line as values break Docker `--env-file` and supervisord. Comments are now on the line above each value.

**Docker container** uses nginx on port **80** → FastAPI **8000**, Next.js **3000**. Override at run time:
`docker run --env-file .env -e CORS_ORIGINS=http://localhost ...`

With `MCP_TRANSPORT=stdio`, `POSTGRES_MCP_PORT` / `CALENDAR_MCP_PORT` are ignored (agents spawn npx directly).

## Known Issues / Human Follow-up
1. **Google Calendar OAuth** — `@franciscpd/calendar-mcp-server` rejects credentials; re-issue refresh token with `calendar.readonly` scope (see `docs/guidence/google-calandar-setup.md`)
2. **Local Node** — host dev uses Node 20; calendar MCP wants Node 22 (Docker has 22)
3. **`.env` passwords** — URL-encode `$` as `%24`; avoid quotes around DATABASE_URL (breaks supervisord)
4. **Docker push** — not run; requires `gh auth` + `docker push ghcr.io/...`

## Next Steps
1. Fix Google OAuth refresh token and re-test full briefing (`POST /api/v1/briefing/generate`)
2. Commit Option 1 changes on a dedicated branch
3. Push image to GHCR when ready (`docker push`)

---

*Last Updated: 31 May 2026*
