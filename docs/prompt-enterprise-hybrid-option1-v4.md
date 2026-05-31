# Option 1 — Enterprise Hybrid: Codebase Audit & Implementation Prompt
**Prompt Version:** 1.0.0
**Architecture Target:** Option 1 — Enterprise Hybrid (Direct MCP per Agent)
**Mode:** Autonomous — Single-Day Delivery with Mandatory Confirmation Gates
**Delivery Goal:** Supabase connected, PostgreSQL MCP wired, Google Calendar MCP wired, full briefing end to end, Docker pushed — today.

---

## HOW TO USE

1. Open a new Cursor chat in **Agent mode**
2. Attach the following before pasting this prompt:
   - `@docs/` (entire folder)
   - `@AGENT.md` (root)
   - `@007-01-ai-daily-briefing-assistant5.md`
   - `@prompts/` (entire folder)
3. Paste the full prompt below the line
4. The agent completes Phase 1 fully and stops at Gate 1
5. Review the audit report — confirm or correct before Phase 2
6. Review the step plan at Gate 2 — confirm before Phase 3 begins
7. Phase 3 is full autonomous implementation through to Docker push

**There are two confirmation gates. The agent must not cross any gate without explicit user approval. If the agent reaches 75% context usage at any point, it must write a checkpoint to `docs/tasks/checkpoint.md` and stop.**

**Phase time budget:** Phase 1 must complete within 30 minutes. Phase 2 within 15 minutes. Phase 3 executes to completion without interruption unless a BLOCKER is encountered.

---

## NON-GOALS — READ FIRST

Before doing anything else, internalise the following constraints. Option 1 must not change any of the following. If any proposed task or change touches these items, flag it as out of scope and stop.

- **Next.js API contract** — all existing endpoint paths, request shapes, and response shapes exposed to the frontend must remain identical
- **Agent prompt content** — the text of system prompts, guardrails, and skills files must not be modified unless the audit finds a direct functional requirement to do so
- **Business logic** — task prioritisation, calendar parsing, focus plan generation, and critic evaluation logic must not change
- **User-facing behaviour** — the briefing output seen by the user must be identical before and after MCP integration
- **Existing passing tests** — no existing passing test may be deleted or modified; only new tests may be added
- **Existing Jira task IDs** — existing task IDs must not be renumbered or reassigned
- **No new internal services** — Option 1 explicitly adds zero new long-running services beyond MCP server processes managed by Supervisord. If any change requires a new FastAPI app, a gateway, or a new Docker container, flag it as out of scope.

---

## TARGET ARCHITECTURE — FIXED

This is the exact topology you are implementing. Do not deviate from it.

```
Next.js
  └── FastAPI (existing — additive changes only)
        └── LangGraph Orchestrator (existing — additive changes only)
              ├── Task Agent ──────────→ mcp-server-postgres (Supervisord process, stdio)
              │                               └── Supabase PostgreSQL (port 6543, Supavisor)
              ├── Calendar Agent ──────→ Google Calendar MCP (Supervisord process, stdio)
              ├── Focus Agent ─────────→ LLM only (no change)
              └── Critic Agent ────────→ LLM only (no change)

SQLAlchemy (async) ──────────────────→ Supabase PostgreSQL (port 6543)
  └── DLQ writes, Alembic migrations, preference storage
  └── Agents NEVER call SQLAlchemy directly — Task Agent uses PostgreSQL MCP only
```

Every change in this prompt is additive. No existing file is deleted. No existing passing behaviour changes.

---

## PROMPT (copy everything below this line)

---

You are a Principal Software Architect and Senior AI Engineer operating in autonomous implementation mode.

You are implementing **Option 1 — Enterprise Hybrid** for the AI Daily Briefing Assistant project as specified in `007-01-ai-daily-briefing-assistant5.md`.

Read and apply the **NON-GOALS** section above before doing anything else. Enforce those constraints throughout every phase.

Read and fix the **TARGET ARCHITECTURE** above. Every implementation decision must be consistent with it.

This prompt has three phases separated by mandatory confirmation gates. Read all phases now to understand the full scope, then execute only Phase 1 until instructed to proceed.

---

## PHASE 1 — EVIDENCE-BASED CODEBASE AUDIT (READ ONLY)

**Goal:** Understand exactly what is broken and what already works. Every finding must be evidence-based — file path, function name, line number. No speculation.

---

### Step 1.1 — Full Source Tree Discovery

Run the following shell commands and record every result. If shell access is unavailable, use Cursor's repository search panel for each keyword group and note which discovery steps could not be completed.

```bash
# Full project tree
find . -type f \
  -not -path '*/.git/*' \
  -not -path '*/node_modules/*' \
  -not -path '*/__pycache__/*' \
  -not -path '*/.venv/*' \
  -not -path '*/dist/*' \
  -not -path '*/.next/*' \
  | sort

# DATABASE_URL — confirm current value or pattern
grep -rn "DATABASE_URL\|database_url\|SUPABASE_URL\|supabase_url" \
  . --include="*.py" --include="*.env*" --include="*.example" \
  --include="docker-compose*.yml"

# SQLAlchemy engine and session creation points
grep -rn "AsyncSession\|create_async_engine\|sessionmaker\|engine\b" \
  backend/ --include="*.py"

# Alembic migration state
find . -name "alembic.ini" -o -name "env.py" -path "*/alembic/*" \
  -o -name "*.py" -path "*/versions/*" | sort

# MCP — every reference in the codebase
grep -rn "mcp\|MCP\|mcp_server\|MCPClient\|mcp_client\|StdioServerParameters\|stdio_client" \
  . --include="*.py" --include="*.ts" --include="*.tsx" \
  --include="*.json" --include="*.yml" --include="*.yaml"

# Supervisord — current process definitions
grep -rn "program:\|command=\|autostart\|autorestart" \
  . --include="*.conf"

# LangGraph — agent nodes and edges
grep -rn "StateGraph\|add_node\|add_edge\|add_conditional_edges\|ainvoke\|astream" \
  backend/ --include="*.py"

# AgentResultEnvelope
grep -rn "AgentResultEnvelope\|agent_result\|escalation\|canonical_role\|status.*success\|status.*failure" \
  backend/ --include="*.py"

# Google Calendar — any existing integration
grep -rn "google\|calendar\|gcal\|GOOGLE_CLIENT\|CALENDAR_ID" \
  . --include="*.py" --include="*.env*" --include="*.example" \
  --include="*.json" --include="*.yml"

# FastAPI routes
grep -rn "@app\.\|@router\.\|APIRouter\|Depends(" \
  backend/ --include="*.py"

# Environment variables — full inventory
grep -rn "os\.environ\|os\.getenv\|settings\.\|BaseSettings" \
  backend/ --include="*.py"

# Async correctness — flag any blocking call in async context
grep -rn "time\.sleep\|requests\.get\|requests\.post\|\.read()\b" \
  backend/ --include="*.py"

# Existing test files
find . \( -name "test_*.py" -o -name "*_test.py" \
  -o -name "*.test.ts" -o -name "*.spec.ts" \) | sort

# Docker and infrastructure
find . \( -name "Dockerfile*" -o -name "docker-compose*.yml" \
  -o -name "supervisord.conf" -o -name "nginx.conf" \) | sort

# Port bindings — confirm no conflicts
grep -rn "5432\|6543\|8000\|8080" \
  . --include="docker-compose*.yml" --include="*.conf" --include="*.env*"

# CI/CD pipeline
find . \( -name "*.yml" -path "*/.github/*" \
  -o -name "*.yml" -path "*/.gitlab-ci*" \) | sort
```

---

### Step 1.2 — Documentation Read Order

After source discovery, read attached documents in this order:

1. `AGENT.md` (root)
2. `docs/ARCHITECTURE.md`
3. `docs/MCP.md`
4. `docs/ENGINEERING-STANDARDS.md`
5. `docs/SECURITY.md`
6. `docs/OBSERVABILITY.md`
7. `007-01-ai-daily-briefing-assistant5.md`
8. All files under `docs/jira-tickets-json/` — record the highest existing task ID

---

### Step 1.3 — Current State vs Target State Comparison

Produce this comparison from source evidence only. Every cell must be filled with a file reference or explicitly marked `NOT FOUND`.

| Component | Target State | Current State | Gap |
|---|---|---|---|
| `DATABASE_URL` | Supabase Supavisor port 6543 | ? (file + line) | Configured / NOT SET / Wrong value |
| Alembic migrations | Run against Supabase, current revision | ? (file + line) | Run / NOT RUN / NO FILE |
| SQLAlchemy async engine | `create_async_engine` with Supavisor URL | ? (file + line) | Correct / Wrong URL / Sync engine |
| `mcp-server-postgres` | Supervisord process, stdio | ? (file + line) | Defined / NOT DEFINED |
| Task Agent → PostgreSQL MCP | Agent calls `pg_query`, `pg_list_tables` via MCP | ? (file + line) | Wired / Stubbed / Direct SQLAlchemy |
| Google Calendar MCP | Supervisord process, stdio | ? (file + line) | Defined / NOT DEFINED |
| Calendar Agent → Calendar MCP | Agent calls `get_events` via MCP | ? (file + line) | Wired / Stubbed / NOT IMPLEMENTED |
| Focus Agent | LLM only — no MCP | ? (file + line) | Working / Stubbed / NOT IMPLEMENTED |
| Critic Agent | LLM only — no MCP | ? (file + line) | Working / Stubbed / NOT IMPLEMENTED |
| Orchestrator | Assembles `AgentResultEnvelope` | ? (file + line) | Working / Stubbed / NOT IMPLEMENTED |
| `AgentResultEnvelope` | Pydantic v2 schema with all fields | ? (file + line) | Implemented / Partial / NOT FOUND |
| LangGraph graph | All five nodes wired, edges defined | ? (file + line) | Complete / Partial / NOT WIRED |
| FastAPI `/briefing` endpoint | Calls LangGraph, returns envelope | ? (file + line) | Working / Stubbed / NOT FOUND |
| Docker build | Single container, all processes | ? | Builds / Fails / NOT TESTED |
| Supervisord | Manages all processes | ? (file + line) | Complete / Missing processes |

---

### Step 1.4 — Audit Dimensions

Every finding: **file path → class/function → line number → finding → severity (BLOCKER / MAJOR / MINOR)**.

---

#### DIMENSION A — Supabase and Database Gap

- Confirm current `DATABASE_URL` — is it a local Postgres URL, a placeholder, or a real Supabase string? File and line.
- Confirm whether the URL uses Supavisor port 6543 (required for connection pooling) or direct port 5432
- List every `create_async_engine` or `sessionmaker` call — file and line
- Confirm whether `asyncpg` is in `pyproject.toml` dependencies — file and line
- Confirm whether Alembic `env.py` is configured for async — file and line
- Confirm whether migration version files exist and what tables they create
- Confirm whether RLS policies exist as SQL files or are documented only
- Confirm whether `pgvector` is referenced anywhere — file and line

**Blockers to identify:**
- Missing `DATABASE_URL` → BLOCKER
- Sync SQLAlchemy engine in async FastAPI context → BLOCKER
- No Alembic migration files → BLOCKER
- `asyncpg` not in dependencies → BLOCKER

---

#### DIMENSION B — PostgreSQL MCP Gap

- Confirm whether `mcp-server-postgres` appears anywhere in `supervisord.conf` — file and line
- Confirm whether `npx @modelcontextprotocol/server-postgres` or equivalent is referenced — file and line
- Confirm whether Task Agent calls any MCP tool (`pg_query`, `pg_list_tables`, `pg_insert`) — file and line
- Confirm whether Task Agent uses direct SQLAlchemy instead of MCP — this is wrong for Option 1 and must be refactored
- Confirm whether the MCP tool schemas in `docs/MCP.md` for PostgreSQL MCP match what the Task Agent expects to receive back
- Confirm whether `MCP_POSTGRES_URL` or equivalent environment variable is defined — file and line

**Blockers to identify:**
- Task Agent uses direct SQLAlchemy (not MCP) → BLOCKER — must refactor
- `mcp-server-postgres` not in Supervisord → BLOCKER
- No `MCP_POSTGRES_URL` env var → BLOCKER

---

#### DIMENSION C — Google Calendar MCP Gap

- Confirm whether any Google Calendar MCP process is defined in `supervisord.conf` — file and line
- Confirm whether `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REFRESH_TOKEN` are in `.env.example` — file and line
- Confirm whether Calendar Agent calls any MCP tool (`list_calendars`, `get_events`) — file and line
- Confirm whether Calendar Agent is stubbed, returning hardcoded data — file and line
- Confirm whether OAuth consent flow is documented in `docs/AGENTIC-CONSENT.md` and whether the token exchange is implemented
- Confirm whether the Google Calendar MCP allowlist (`*.googleapis.com`) is enforced anywhere in code — file and line

**Blockers to identify:**
- Calendar Agent fully stubbed → BLOCKER — must refactor
- No Google OAuth credentials in `.env.example` → BLOCKER
- Google Calendar MCP not in Supervisord → BLOCKER

---

#### DIMENSION D — Agent Implementation State

For each agent confirm:
- Implemented as a real LangGraph node (file and line) or a stub returning hardcoded data
- `AgentResultEnvelope` constructed with all required fields — file and line
- Circuit breaker or token budget check present — file and line or ABSENT
- `prompt_version` field populated in envelope — file and line or ABSENT

| Agent | Node implemented | Envelope populated | Circuit breaker | prompt_version |
|---|---|---|---|---|
| Task Agent | YES/STUB (file, line) | YES/NO | YES/NO | YES/NO |
| Calendar Agent | YES/STUB (file, line) | YES/NO | YES/NO | YES/NO |
| Focus Agent | YES/STUB (file, line) | YES/NO | YES/NO | YES/NO |
| Critic Agent | YES/STUB (file, line) | YES/NO | YES/NO | YES/NO |
| Orchestrator | YES/STUB (file, line) | YES/NO | YES/NO | YES/NO |

---

#### DIMENSION E — LangGraph Wiring

- Reconstruct the full node and edge graph from source:

```
StateGraph defined at: [file, line]
Nodes:
  - [node name] → [function] (file, line)
  ...
Edges:
  - [from] → [to] (file, line)
  ...
Conditional edges:
  - [from] → [condition function] → {[result]: [to], ...} (file, line)
```

- Confirm whether the graph is compiled and called from the FastAPI endpoint — file and line
- Confirm whether the graph handles partial agent failure (some nodes fail, orchestrator still assembles envelope) — file and line or ABSENT
- Flag any node that is defined but not wired into any edge as MAJOR

---

#### DIMENSION F — Infrastructure and Deployment State

- `docker-compose.yml` — list every service; confirm whether all required processes are present
- `Dockerfile` — confirm base image, build steps, whether `npm` is available for `npx mcp-server-postgres`
- `supervisord.conf` — list every `[program:X]` block; confirm what is missing for Option 1
- `nginx.conf` — confirm upstream and location blocks are correct for current FastAPI port
- `.env.example` — list every variable; identify which are missing for Option 1 (Supabase URL, Google OAuth, MCP paths)
- CI/CD pipeline — confirm whether Docker build step exists and which registry it targets

**New environment variables required for Option 1** (confirm each is absent before adding):
```
DATABASE_URL=postgresql+asyncpg://[user]:[password]@[host]:6543/[db]?sslmode=require
MCP_POSTGRES_URL=postgresql://[user]:[password]@[host]:6543/[db]?sslmode=require
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
GOOGLE_REFRESH_TOKEN=
CALENDAR_ID=primary
```

---

#### DIMENSION G — Security Boundary Check

- Confirm whether the Google Calendar MCP allowlist (`*.googleapis.com`) is enforced in code — file and line
- Confirm whether PostgreSQL MCP connection string is read from environment only — no hardcoded credentials
- Confirm whether any secret appears in logs, traces, or `AgentResultEnvelope`
- Confirm whether JWT from Next.js is validated at the FastAPI endpoint — file and line
- Confirm whether Supabase RLS policies are enforced — SQL file or DOCUMENTED ONLY

---

#### DIMENSION H — Async Correctness

- List every `time.sleep`, synchronous `requests.get`, or synchronous `requests.post` call in `backend/` — file and line; each is a BLOCKER
- Confirm every SQLAlchemy session is opened with `async with AsyncSession` — file and line
- Confirm every MCP client call uses `await` — file and line or ABSENT

---

#### DIMENSION I — Existing Jira Coverage

- Every existing epic: ID, title, status
- Every task that covers Supabase connection, PostgreSQL MCP, or Google Calendar MCP — superseded or still valid
- Highest existing task ID — for new ID sequencing
- Tasks that are complete today and need no further work — list them so Phase 3 skips them

---

### Step 1.5 — Delivery Risk Assessment

Answer each question with evidence. This feeds directly into the Phase 2 step plan.

| Risk | Evidence | Severity | Blocker for today |
|---|---|---|---|
| Supabase project not yet created | No real connection string in .env | ? | YES / NO |
| Google OAuth credentials not issued | Missing from .env.example | ? | YES / NO |
| Task Agent uses direct SQLAlchemy (needs MCP refactor) | ? | ? | YES / NO |
| Calendar Agent fully stubbed | ? | ? | YES / NO |
| LangGraph graph incomplete or unwired | ? | ? | YES / NO |
| Docker build currently failing | ? | ? | YES / NO |
| Alembic has no migration files | ? | ? | YES / NO |
| `asyncpg` missing from dependencies | ? | ? | YES / NO |
| Focus or Critic Agent not implemented | ? | ? | YES / NO |

Fill every cell. A YES in the final column means it must be resolved in Phase 3 today.

---

### Phase 1 Output — Audit Report

```
## AUDIT REPORT — Option 1 Enterprise Hybrid Readiness
## Prompt Version: 1.0.0
## Generated: [date]
## Codebase State: [git commit hash or "unavailable"]
## Discovery Method: [shell commands / file indexing / partial — specify]
## Phase 1 Time Used: [minutes]

### CURRENT STATE vs TARGET STATE TABLE
[All rows filled with file references]

### DIMENSION A — Supabase and Database Gaps
[file → function → line → finding → severity]

### DIMENSION B — PostgreSQL MCP Gaps
[file → function → line → finding → severity]

### DIMENSION C — Google Calendar MCP Gaps
[file → function → line → finding → severity]

### DIMENSION D — Agent Implementation State Table
[All rows filled]

### DIMENSION E — LangGraph Wiring
[Reconstructed node and edge graph]
[Gap findings]

### DIMENSION F — Infrastructure State
[Per file: current state → what must be added]
[Missing env vars listed]

### DIMENSION G — Security Boundary Check
[Per item: CONFIRMED / ABSENT / DOCUMENTED ONLY]

### DIMENSION H — Async Correctness
[Blocking calls listed — each is a BLOCKER]

### DIMENSION I — Jira Coverage
[Existing epics and tasks]
[Highest existing ID: DB-XXX]
[Tasks already complete — skip list for Phase 3]

### DELIVERY RISK TABLE
[All rows filled]

### BLOCKER SUMMARY
[Numbered list of all BLOCKERs — these are the exact items Phase 3 must fix]

### READINESS SCORE (0–10 per dimension)
[A through I with one-line justification]
[Overall: X/10]
[Estimated Phase 3 implementation hours based on blocker count]
```

---

**CONFIRMATION GATE 1**
Stop. Do not proceed to Phase 2 until the user explicitly confirms the audit report. If the phase time budget was exceeded, list which dimensions are incomplete.

---

## PHASE 2 — STEP PLAN AND EFFORT ESTIMATE

**Goal:** Produce the exact ordered implementation plan for today. No ADR. No epic planning. Just the nine steps that get you to a working Docker push by end of day.

---

### Step 2.1 — Ordered Implementation Plan

Produce this table. Populate effort from audit findings. Mark each step as BLOCKED (depends on a human action outside the codebase, e.g. creating a Supabase project) or AUTOMATED (agent can complete it without human input).

| # | Step | Type | Effort | Depends On | Parallelisable With |
|---|---|---|---|---|---|
| 1 | Create Supabase project — copy Supavisor connection string (port 6543) | BLOCKED — human action | 10 min | — | — |
| 2 | Set `DATABASE_URL` and `MCP_POSTGRES_URL` in `.env` | BLOCKED — human action | 2 min | Step 1 | — |
| 3 | Add `asyncpg` to `pyproject.toml` if missing; confirm `uv sync` | AUTOMATED | S | Step 2 | Step 8 |
| 4 | Fix Alembic `env.py` for async if needed; run migrations against Supabase | AUTOMATED | S | Step 2 | — |
| 5 | Add `mcp-server-postgres` as Supervisord process; wire Task Agent to call PostgreSQL MCP tools | AUTOMATED | M | Step 2 | Step 6 |
| 6 | Issue Google OAuth credentials — copy to `.env` | BLOCKED — human action | 15 min | — | Step 5 |
| 7 | Add Google Calendar MCP as Supervisord process; wire Calendar Agent to call it | AUTOMATED | M | Step 6 | — |
| 8 | Confirm Focus Agent and Critic Agent are implemented or fix stubs | AUTOMATED | S–M | — | Step 3 |
| 9 | Run full briefing end to end — confirm `AgentResultEnvelope` from all five agents | AUTOMATED | S | Steps 5,7,8 | — |
| 10 | Docker build, smoke test, push | AUTOMATED | S | Step 9 | — |

**BLOCKED steps require human action before the agent can proceed. The agent must stop at each BLOCKED step and wait for confirmation that the human action is complete before continuing.**

---

### Step 2.2 — Pre-Implementation Checklist

Before Phase 3 begins, the following must be true. Confirm each from the audit findings.

```
PRE-IMPLEMENTATION CHECKLIST

□ Supabase project exists and connection string is in .env (BLOCKED — human)
□ Google OAuth credentials are in .env (BLOCKED — human)
□ asyncpg is in pyproject.toml
□ Alembic env.py is async-compatible
□ No time.sleep or synchronous requests calls remain in backend/ (fix if found)
□ AgentResultEnvelope schema is defined as Pydantic v2 model
□ LangGraph StateGraph is defined with at least placeholder nodes for all five agents
□ FastAPI /briefing endpoint exists and calls the LangGraph graph
□ supervisord.conf exists and manages the FastAPI process
□ Dockerfile builds without error (run: docker build --no-cache -t briefing:test .)
```

Items marked BLOCKED require the user to confirm completion before the agent proceeds.

---

### Phase 2 Output — Step Plan

```
## STEP PLAN — Option 1 Enterprise Hybrid
## Prompt Version: 1.0.0
## Generated: [date]

### ORDERED IMPLEMENTATION STEPS
[Table from Step 2.1 — all rows filled with effort from audit]

### HUMAN ACTIONS REQUIRED BEFORE PHASE 3
[Numbered list: exactly what the user must do manually before confirming Gate 2]
1. Create Supabase project at https://supabase.com — copy the Supavisor connection string (Settings → Database → Connection string → URI, port 6543). Paste into .env as DATABASE_URL and MCP_POSTGRES_URL.
2. Create Google Cloud OAuth 2.0 credentials at https://console.cloud.google.com — enable Google Calendar API, create OAuth client ID (Desktop app), complete consent flow, copy refresh token. Paste GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REFRESH_TOKEN into .env.

### ESTIMATED TOTAL IMPLEMENTATION TIME
[Hours — automated steps only, excluding BLOCKED human actions]

### PARALLELISABLE GROUPS
[Steps that can run concurrently once their dependencies are met]
```

---

**CONFIRMATION GATE 2**
Stop. Do not proceed to Phase 3 until:
1. The user confirms the step plan is correct
2. The user confirms that all BLOCKED human actions are complete (Supabase project created, `.env` populated, Google OAuth credentials in `.env`)

The agent must ask explicitly: "Have you completed the Supabase setup and Google OAuth credential steps? Please confirm before I begin implementation."

---

## PHASE 3 — FULL AUTONOMOUS IMPLEMENTATION

**Goal:** Execute all AUTOMATED steps from the Phase 2 step plan in order. Deliver a working Docker push by end of session.

---

### Step 3.1 — Pre-Implementation Verification

Before writing a single line of code, run the following checks. All must pass.

```bash
# Confirm DATABASE_URL is set and reachable
python -c "import os; url = os.getenv('DATABASE_URL'); assert url and 'supabase' in url.lower() or '6543' in url, 'DATABASE_URL not set or not pointing to Supabase'"

# Confirm asyncpg is importable
python -c "import asyncpg; print('asyncpg OK')"

# Confirm uv environment is up to date
uv sync

# Confirm Docker daemon is running
docker info > /dev/null && echo "Docker OK"

# Confirm supervisord.conf exists
test -f infrastructure/supervisord.conf && echo "supervisord.conf found" || echo "MISSING"

# Confirm .env has required variables
grep -q "DATABASE_URL" .env && echo "DATABASE_URL present" || echo "DATABASE_URL MISSING"
grep -q "GOOGLE_CLIENT_ID" .env && echo "GOOGLE_CLIENT_ID present" || echo "GOOGLE_CLIENT_ID MISSING"
grep -q "MCP_POSTGRES_URL" .env && echo "MCP_POSTGRES_URL present" || echo "MCP_POSTGRES_URL MISSING"
```

If any check fails, stop and report. Do not proceed until all pass.

---

### Step 3.2 — Execute Implementation Steps in Order

Execute each AUTOMATED step from the Phase 2 plan. For each step:

1. State which step you are starting (e.g. "Starting Step 3 — asyncpg dependency")
2. Make the change
3. Run any relevant verification command
4. State the step is complete before moving to the next

---

#### STEP 3 — Dependency and Alembic Fix

If `asyncpg` is not in `pyproject.toml`:
```bash
uv add asyncpg
```

If Alembic `env.py` uses a synchronous engine, replace with async pattern:

```python
# backend/alembic/env.py — async pattern
from sqlalchemy.ext.asyncio import create_async_engine
import asyncio

def run_migrations_online():
    connectable = create_async_engine(settings.DATABASE_URL)

    async def run():
        async with connectable.connect() as connection:
            await connection.run_sync(do_run_migrations)

    asyncio.run(run())
```

Run migrations:
```bash
cd backend && alembic upgrade head
```

Confirm output shows tables created against Supabase. If migration files do not exist, create an initial migration:
```bash
alembic revision --autogenerate -m "initial_schema"
alembic upgrade head
```

---

#### STEP 4 — PostgreSQL MCP: Supervisord Process

Add to `infrastructure/supervisord.conf`:

```ini
[program:mcp-postgres]
command=npx -y @modelcontextprotocol/server-postgres %(ENV_MCP_POSTGRES_URL)s
autostart=true
autorestart=true
stderr_logfile=/var/log/mcp-postgres.err.log
stdout_logfile=/var/log/mcp-postgres.out.log
environment=MCP_POSTGRES_URL="%(ENV_MCP_POSTGRES_URL)s"
```

Confirm `npm` / `npx` is available in the Docker image. If not, add to `Dockerfile`:
```dockerfile
RUN apt-get update && apt-get install -y nodejs npm
```

---

#### STEP 5 — Task Agent: Wire to PostgreSQL MCP

The Task Agent must call MCP tools — not SQLAlchemy directly. Apply this pattern:

```python
# backend/agents/task/agent.py
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def run_task_agent(state: BriefingState) -> AgentResultEnvelope:
    server_params = StdioServerParameters(
        command="npx",
        args=["-y", "@modelcontextprotocol/server-postgres", settings.MCP_POSTGRES_URL],
    )
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool(
                "query",
                arguments={"sql": "SELECT * FROM tasks WHERE done = false ORDER BY priority DESC LIMIT 10"}
            )
    # Parse result.content into task list
    # Return AgentResultEnvelope
```

Ensure the `AgentResultEnvelope` is populated with all required fields:
```python
return AgentResultEnvelope(
    agent_id="task",
    canonical_role="doer",
    status="success",
    result={"tasks": parsed_tasks},
    metadata=AgentMetadata(
        execution_ms=elapsed,
        tokens_used=0,
        model_used="none",
        prompt_version=settings.PROMPT_VERSION,
        trace_id=state.trace_id,
        data_classification="confidential_pii",
    )
)
```

---

#### STEP 6 — Google Calendar MCP: Supervisord Process

Add to `infrastructure/supervisord.conf`:

```ini
[program:mcp-google-calendar]
command=npx -y @anthropic-ai/mcp-server-google-calendar
autostart=true
autorestart=true
stderr_logfile=/var/log/mcp-calendar.err.log
stdout_logfile=/var/log/mcp-calendar.out.log
environment=GOOGLE_CLIENT_ID="%(ENV_GOOGLE_CLIENT_ID)s",GOOGLE_CLIENT_SECRET="%(ENV_GOOGLE_CLIENT_SECRET)s",GOOGLE_REFRESH_TOKEN="%(ENV_GOOGLE_REFRESH_TOKEN)s",CALENDAR_ID="%(ENV_CALENDAR_ID)s"
```

**Note:** Confirm the exact package name for the Google Calendar MCP server from `docs/MCP.md`. If a different package is specified there, use that. Do not guess.

---

#### STEP 7 — Calendar Agent: Wire to Google Calendar MCP

Apply the same `stdio_client` pattern as Step 5. The Calendar Agent calls `get_events` with today's date range:

```python
result = await session.call_tool(
    "get_events",
    arguments={
        "calendar_id": settings.CALENDAR_ID,
        "time_min": today_start_iso,
        "time_max": today_end_iso,
    }
)
```

Enforce the SSRF allowlist at the environment level — the MCP server only communicates with `*.googleapis.com`. No additional code is required if the MCP server package enforces this natively. Confirm from `docs/MCP.md` whether application-level enforcement is also required.

---

#### STEP 8 — Focus Agent and Critic Agent: Confirm or Fix

For each of Focus Agent and Critic Agent:

- If the agent is a real LangGraph node calling an LLM — confirm it returns a valid `AgentResultEnvelope` and move on
- If the agent is a stub returning hardcoded data — implement it as a real LLM call using the existing prompt from `prompts/focus/system.md` and `prompts/critic/system.md`
- Do not modify the prompt content — use it exactly as written

---

#### STEP 9 — End-to-End Briefing Test

Run the full briefing and confirm all five envelopes are returned:

```bash
# Start all processes
supervisord -c infrastructure/supervisord.conf

# Wait for MCP servers to start
sleep 3

# Trigger briefing
curl -s -X POST http://localhost:8000/api/v1/briefing \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TEST_JWT" \
  -d '{}' | python -m json.tool
```

Confirm the response contains:
```json
{
  "agents": {
    "task": {"status": "success"},
    "calendar": {"status": "success"},
    "focus": {"status": "success"},
    "critic": {"status": "success"},
    "orchestrator": {"status": "success"}
  }
}
```

If any agent returns `"status": "failure"`, fix it before proceeding to Step 10. Do not push a failing build.

---

#### STEP 10 — Docker Build, Smoke Test, Push

```bash
# Build
docker build --no-cache -t briefing:latest .

# Smoke test — run container, trigger one briefing
docker run --env-file .env -p 8000:8000 briefing:latest &
sleep 5
curl -s http://localhost:8000/health | python -m json.tool
curl -s -X POST http://localhost:8000/api/v1/briefing \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TEST_JWT" \
  -d '{}' | python -m json.tool

# Push — confirm registry target from CI config
docker tag briefing:latest $REGISTRY/briefing:latest
docker push $REGISTRY/briefing:latest
```

If the Docker build fails, fix the error before pushing. Common issues:
- `npx` not available → add `nodejs npm` to Dockerfile
- `asyncpg` not installed in image → confirm it is in `pyproject.toml` and `uv sync` runs in Dockerfile
- Environment variables not passed → confirm `--env-file .env` is used or variables are in `docker-compose.yml`

---

### Step 3.3 — Post-Implementation Verification

After Docker push, confirm the following:

```
POST-IMPLEMENTATION CHECKLIST

□ All five AgentResultEnvelopes return status: "success" in end-to-end test
□ Docker image builds without error
□ Docker smoke test passes (health check + one briefing)
□ Image pushed to registry
□ No hardcoded credentials in any committed file
□ .env is in .gitignore — confirm
□ supervisord.conf has correct [program:] blocks for mcp-postgres and mcp-google-calendar
□ alembic upgrade head ran successfully against Supabase
□ All existing passing tests still pass: pytest backend/tests/
```

---

### Step 3.4 — New Jira Tasks (Additive Only)

After implementation is complete, add new task JSON files to `docs/jira-tickets-json/`. New IDs start from the highest ID confirmed in Dimension I plus one. Use the exact JSON schema of existing files.

Create tasks only for work actually completed today that was not already covered by existing tasks:

- Supabase connection wiring (if not covered)
- PostgreSQL MCP Supervisord process (if not covered)
- Task Agent MCP refactor (if not covered)
- Google Calendar MCP Supervisord process (if not covered)
- Calendar Agent MCP wiring (if not covered)
- End-to-end briefing test (if not covered)

Each task JSON must include: `id`, `type`, `summary`, `description`, `acceptance_criteria` (minimum three), `story_points`, `labels`, `epic_link`, `dependencies`.

---

### Step 3.5 — Autonomous Workflow Rules

```
Branch per epic:
1. git checkout epic/autonomus-implementation && git pull
2. git checkout -b epic/E[N]-[slug]
3. Coding Agent    → implement
4. Refactor Agent  → quality check
5. Testing Agent   → add tests
6. Docs Agent      → update AGENT.md files
7. CI must pass
8. git merge commit → epic/autonomus-implementation (no squash, no rebase)
9. Delete local epic branch, keep remote
```

**Context management:** At 75% context usage, write checkpoint to `docs/tasks/checkpoint.md` and stop.

**Standards:**
- All new code async-first — no `time.sleep`, no synchronous `requests` in async context
- All secrets from environment variables only — never hardcoded
- Do not modify existing passing tests — only add new ones
- Do not touch Next.js API contract, agent prompt content, or business logic
- British English in all documentation, no contractions

---

*Prompt Version: 1.0.0 — Option 1 Enterprise Hybrid — May 2026*
