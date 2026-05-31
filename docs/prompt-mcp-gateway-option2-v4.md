# Option 2 — API-First MCP Gateway: Codebase Audit & Implementation Prompt
**Prompt Version:** 4.0.0
**Architecture Target:** Option 2 — API-First MCP Gateway
**Mode:** Autonomous — Phased Execution with Mandatory Confirmation Gates

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
5. Review the audit report and confirm to proceed to Phase 2
6. Review the ADR, effort estimates, and architecture validation at Gate 2 and Gate 2.5
7. Confirm to proceed to Phase 3 only after all gates are cleared

**There are four confirmation gates. The agent must not cross any gate without explicit user approval. If the agent reaches 75% context usage at any point, it must write a checkpoint to `docs/tasks/checkpoint.md` and stop regardless of gate position.**

**Phase time budget:** Phase 1 must complete within 60 minutes of wall-clock autonomous execution. Phase 2 within 30 minutes. If a phase exceeds its budget, stop, write a checkpoint, and report which dimensions or steps are incomplete.

---

## NON-GOALS — READ FIRST

Before doing anything else, internalise the following constraints. Option 2 must not change any of the following. If any proposed task or change touches these items, flag it as out of scope and stop.

- **Next.js API contract** — all existing endpoint paths, request shapes, and response shapes exposed to the frontend must remain identical
- **Agent prompt content** — the text of system prompts, guardrails, and skills files must not be modified unless the audit finds a direct functional requirement to do so; any such change must be explicitly flagged and approved
- **Business logic** — task prioritisation, calendar parsing, focus plan generation, and critic evaluation logic must not change
- **User-facing behaviour** — the briefing output seen by the user must be identical before and after the gateway is introduced
- **Existing passing tests** — no existing passing test may be deleted or modified to make it pass; only new tests may be added
- **Existing Jira task IDs** — existing task IDs must not be renumbered or reassigned

Any work that would touch these areas is a scope-creep risk. Flag it, document it, and require explicit user approval before proceeding.

---

## GATEWAY SCHEMA CONTRACT — READ BEFORE PHASE 1

Before auditing the codebase, define the structural contract the gateway must enforce. This contract governs Dimension J, Gate 2.5 validation, and the Step 3.1 file tree. Any audit finding that conflicts with this contract is a BLOCKER.

```python
# backend/mcp_gateway/schemas/contract.py
# This is the canonical gateway wire format.
# Agents send GatewayToolRequest. Gateway returns GatewayToolResponse.
# No raw dicts may cross the gateway boundary in either direction.

from pydantic import BaseModel, Field
from typing import Any, Literal

class GatewayToolRequest(BaseModel):
    tool: str                          # e.g. "pg_query", "calendar_get_events"
    mcp_server: str                    # e.g. "postgresql", "google_calendar"
    payload: dict[str, Any]            # tool-specific args — validated per tool in schemas/requests.py
    trace_id: str                      # OTel traceparent — REQUIRED
    agent_id: str                      # canonical agent identifier
    mcp_protocol_version: str = "2025-03-26"   # MCP spec version — must match registered server

class GatewayToolResponse(BaseModel):
    tool: str
    mcp_server: str
    result: dict[str, Any]             # tool-specific response — validated per tool in schemas/responses.py
    gateway_trace_id: str              # gateway-assigned span ID
    execution_ms: int
    mcp_protocol_version: str          # echoed from request — drift detection
    status: Literal["success", "failure", "circuit_open", "ssrf_blocked", "injection_detected"]
```

**MCP protocol version note:** The MCP specification reached stable at `2025-03-26`. Audit Dimension J must confirm all MCP server integrations declare a compatible version. Any server advertising a pre-stable version (`2024-11-05` or earlier) is flagged as MAJOR. A version mismatch between `GatewayToolRequest.mcp_protocol_version` and the registered server's declared version is a BLOCKER.

---

## PROMPT (copy everything below this line)

---

You are a Principal Software Architect and Senior AI Engineer operating in autonomous implementation mode.

You are implementing **Option 2 — API-First MCP Gateway** for the AI Daily Briefing Assistant project as specified in `007-01-ai-daily-briefing-assistant5.md`.

Read and apply the **NON-GOALS** section above before doing anything else. Enforce those constraints throughout every phase.

Read and internalise the **GATEWAY SCHEMA CONTRACT** section above. This contract is fixed. Do not propose changes to it. Use it as the reference for all schema compatibility findings in Dimension J.

This prompt has three phases separated by mandatory confirmation gates. Read all phases now to understand the full scope, then execute only Phase 1 until instructed to proceed.

---

## PHASE 1 — EVIDENCE-BASED CODEBASE AUDIT (READ ONLY)

---

### Step 1.1 — Full Source Tree Discovery

**Primary method — shell commands:**

Run the following commands and record every result. If a command fails or shell access is unavailable, fall back to the repository search and file indexing method described below.

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

# Python imports and module dependencies
grep -r "^import\|^from" backend/ --include="*.py" -n

# MCP-related references across entire codebase
grep -rn "mcp\|MCP\|model_context_protocol\|mcp_server\|MCPClient\|mcp_client" \
  . --include="*.py" --include="*.ts" --include="*.tsx" \
  --include="*.json" --include="*.yml" --include="*.yaml"

# MCP protocol version declarations
grep -rn "2024-11-05\|2025-03-26\|mcp_protocol_version\|protocol_version\|MCP_VERSION" \
  . --include="*.py" --include="*.ts" --include="*.json" --include="*.yml"

# SQLAlchemy and database access points
grep -rn "AsyncSession\|create_async_engine\|sessionmaker\|DATABASE_URL\|supabase\|Supavisor\|pgvector" \
  backend/ --include="*.py"

# Agent call graph — LangGraph node and edge definitions
grep -rn "StateGraph\|add_node\|add_edge\|compiled\|ainvoke\|astream\|@graph\|CompiledGraph" \
  backend/ --include="*.py"

# FastAPI route and dependency definitions
grep -rn "@app\.\|@router\.\|APIRouter\|Depends(" \
  backend/ --include="*.py"

# AgentResultEnvelope usage
grep -rn "AgentResultEnvelope\|agent_result\|escalation\|canonical_role" \
  backend/ --include="*.py"

# Environment variable references
grep -rn "os\.environ\|os\.getenv\|settings\.\|BaseSettings\|model_config" \
  backend/ --include="*.py"

# Authentication and JWT references
grep -rn "jwt\|JWT\|Bearer\|Authorization\|verify_token\|decode_token\|pyjwt" \
  . --include="*.py" --include="*.ts" --include="*.tsx" -l

# Docker and infrastructure files
find . \( -name "Dockerfile*" -o -name "docker-compose*.yml" \
  -o -name "supervisord.conf" -o -name "nginx.conf" \
  -o -name "*.tf" -o -name "*.tfvars" \) | sort

# CI/CD pipeline files
find . \( -name "*.yml" -path "*/.github/*" \
  -o -name "*.yml" -path "*/.gitlab-ci*" \) | sort

# Existing test files
find . \( -name "test_*.py" -o -name "*_test.py" \
  -o -name "*.test.ts" -o -name "*.spec.ts" \) | sort

# Secret and credential surface
grep -rn "SECRET\|API_KEY\|TOKEN\|PASSWORD\|CREDENTIAL\|PRIVATE_KEY" \
  . --include="*.env*" --include="*.example" \
  --include="docker-compose*.yml"

# Health check definitions
grep -rn "healthcheck\|/health\|/ready\|/live\|lifespan" \
  . --include="*.yml" --include="*.py" --include="*.ts"

# Outbound HTTP calls
grep -rn "httpx\|aiohttp\|requests\.\|fetch(\|axios" \
  backend/ --include="*.py"

# Port bindings — confirm port 8001 is free
grep -rn "8001\|8000\|8080\|5432\|6543" \
  . --include="docker-compose*.yml" --include="*.conf" --include="*.env*"

# Async correctness — confirm no blocking calls in async context
grep -rn "time\.sleep\|requests\.get\|requests\.post\|\.read()\b" \
  backend/ --include="*.py"

# Parallelisable work surface — confirm which agents have no cross-dependencies
grep -rn "StateGraph\|add_edge\|add_conditional_edges" \
  backend/ --include="*.py" -A 5
```

**Fallback method — if shell access is unavailable:**

Use Cursor's built-in repository search and file indexing to locate the same information. Search for each keyword group listed above using the IDE search panel. Record every match with file path and line number. Note in the audit report that shell commands were unavailable and file indexing was used instead. If neither method is fully available, document exactly which discovery steps could not be completed and mark affected audit dimensions as **PARTIAL — MANUAL VERIFICATION REQUIRED**.

Every finding in the audit report must cite a specific file path, class name, function name, and line number where applicable. Speculative findings without evidence are not permitted.

---

### Step 1.2 — Documentation Read Order

After completing source discovery, read attached documents in this order:

1. `AGENT.md` (root)
2. `docs/ARCHITECTURE.md`
3. `docs/MCP.md`
4. `docs/ENGINEERING-STANDARDS.md`
5. `docs/SECURITY.md`
6. `docs/OBSERVABILITY.md`
7. `docs/AGENTIC-CONSENT.md`
8. `007-01-ai-daily-briefing-assistant5.md`
9. All files under `prompts/`
10. All files under `docs/jira-tickets-json/` — record the highest existing task ID

---

### Step 1.3 — Architecture Comparison

Before auditing gaps, produce an explicit comparison of the three architecture states. This comparison is required input for the ADR in Phase 2.

#### Current Architecture (from source evidence)

Reconstruct the actual current architecture from source code — not from documentation. Show:

```
[Reconstruct from source — file references per node]
Next.js
  └── FastAPI (file: ?, line: ?)
        └── LangGraph (file: ?, line: ?)
              ├── Agent → MCP call (file: ?, line: ?)
              └── Agent → DB call (file: ?, line: ?)
```

State clearly: what works today, what is stubbed, what is missing entirely.

#### Option 1 — Enterprise Hybrid (Direct MCP per Agent)

```
Next.js
  └── FastAPI
        ├── LangGraph Orchestrator
        │     ├── Task Agent ──────────→ PostgreSQL MCP (direct)
        │     ├── Calendar Agent ──────→ Google Calendar MCP (direct)
        │     ├── Focus Agent ─────────→ LLM only
        │     └── Critic Agent ────────→ LLM only
        └── SQLAlchemy (async) ────────→ Supabase PostgreSQL
```

For each agent call: estimate latency, security boundary count, observability coverage.

#### Option 2 — API-First MCP Gateway (Target)

```
Next.js
  └── FastAPI
        ├── LangGraph Orchestrator
        │     ├── Task Agent ──────────→ MCP Gateway (port 8001)
        │     │                               └── PostgreSQL MCP → Supabase (port 6543)
        │     ├── Calendar Agent ──────→ MCP Gateway (port 8001)
        │     │                               └── Google Calendar MCP
        │     ├── Focus Agent ─────────→ LLM only (no MCP — by design)
        │     ├── Critic Agent ────────→ MCP Gateway (port 8001)
        │     │                               └── Injection scan tool
        │     └── Orchestrator ────────→ AgentResultEnvelope → Next.js
        └── SQLAlchemy (async) ────────→ Supabase PostgreSQL (port 6543)
              └── writes, DLQ, migrations only
```

For each agent call: estimate latency, security boundary count, observability coverage.

#### Comparison Summary Table

| Dimension | Current State | Option 1 | Option 2 |
|---|---|---|---|
| MCP auth boundaries | ? | 1 per agent | 1 central |
| SSRF enforcement points | ? | 1 per agent | 1 central |
| OTel span coverage | ? | per agent | per tool call |
| Security audit surface | ? | distributed | centralised |
| New service required | No | No | Yes (gateway) |
| Latency overhead | baseline | baseline | +gateway hop |
| Agent refactor required | — | minimal | moderate |
| Rollback complexity | — | low | medium |
| MCP protocol version enforcement | ? | per agent | 1 central |
| Parallelisable agent paths | ? | ? | ? |

Fill every cell with evidence from source discovery. Use "?" only if genuinely undetectable.

---

### Step 1.4 — Audit Dimensions

Every finding must state: **file path → class/function → line number → finding → severity (BLOCKER / MAJOR / MINOR)**.

---

#### DIMENSION A — MCP Implementation Gap Analysis

- List every MCP server referenced in documentation versus every MCP server instantiated or called in source code
- For each agent, trace every outbound tool call: file, function, line, MCP tool name
- Confirm whether a gateway, router, or registry exists anywhere in `backend/` — evidence required
- Confirm whether MCP tool schemas in `docs/MCP.md` match actual call signatures in code — see Dimension J for full schema compatibility audit
- Confirm whether SSRF allowlists are enforced in code or only documented
- Confirm whether MCP connections use hardcoded URLs or resolved config
- **MCP protocol version audit:** For every MCP server integration found, record the declared MCP protocol version. Flag any server on pre-stable `2024-11-05` as MAJOR. Flag any server with no declared version as MAJOR. Record findings for Dimension J cross-reference.

---

#### DIMENSION B — Supabase PostgreSQL Gap Analysis

- Confirm current `DATABASE_URL` value or pattern — file and line
- Confirm whether Supavisor port 6543 is configured — file and line
- List every SQLAlchemy engine or session creation point — file and line
- Confirm whether RLS policies exist as SQL migration files or Supabase config
- Confirm whether `pgvector` is referenced in migrations, models, or requirements
- Confirm whether Alembic async migration files exist and their current revision state

---

#### DIMENSION C — Agent Architecture and Call Graph

Reconstruct the complete call graph from source evidence:

```
FastAPI endpoint (file, line)
  └── LangGraph graph (file, line)
        ├── Orchestrator node (file, line)
        ├── Task Agent node (file, line) → tool calls (file, line)
        ├── Calendar Agent node (file, line) → tool calls (file, line)
        ├── Focus Agent node (file, line)
        └── Critic Agent node (file, line) → tool calls (file, line)
```

For each agent confirm:
- `AgentResultEnvelope` implemented and used consistently — file and line
- Circuit breakers and token budget enforcement — implemented or only specified
- LangGraph edges and conditional routing — wired correctly or missing
- All five agents implemented or partially stubbed
- **Parallelism surface:** Identify which agents have no data dependency on each other's output and could run concurrently in a `Send` / parallel LangGraph branch. Record as an advisory finding — do not implement in this prompt without explicit approval.

---

#### DIMENSION D — Security Boundary Verification

**Authentication propagation**
- How does the JWT from Next.js reach FastAPI — file and line
- Does the JWT propagate into LangGraph agent calls — file and line
- Does any agent or MCP call carry an identity token — evidence required

**Authorisation checks**
- Where are RBAC checks enforced — file and line
- Are Supabase RLS policies enforced at connection level or assumed only
- Does the Critic Agent have authorisation scope restrictions

**Secret management**
- Every location where API keys, tokens, or credentials are loaded — file and line
- Confirm secrets are from environment variables only — no hardcoded values
- Confirm no secret appears in logs, traces, or `AgentResultEnvelope`

**Service-to-service trust boundaries**
- Every internal service-to-service HTTP call — file and line
- Whether internal calls use mutual TLS, shared secret headers, or no authentication
- Whether MCP server connections validate caller identity

**Outbound network restrictions**
- Every outbound HTTP call beyond MCP allowlists — file and line
- Whether Docker network config enforces egress restrictions

---

#### DIMENSION E — Deployment Impact Assessment

Audit every infrastructure file for changes required to introduce the MCP Gateway:

- `docker-compose.yml` — every service defined; what must be added for gateway; confirm port 8001 is not already bound
- `Dockerfile` — single multi-service image or separate images; determine which model applies
- `supervisord.conf` — every process defined; where gateway process would be added
- `nginx.conf` — every upstream and location block; whether gateway needs reverse proxy entry
- Environment variable inventory — every variable required by gateway that does not exist yet
- Health check requirements — what endpoint the gateway must expose (`GET /health` returning `{"status": "ok", "mcp_servers": [...]}`)
- Kubernetes manifests — whether any exist and whether they need updating
- CI/CD pipeline — every step that touches deployment configuration

**MCP Gateway deployment model determination:**

Based on the above findings, recommend exactly one deployment model and justify it:

- **Model A — FastAPI sub-app** mounted at `/mcp-gateway` on the existing FastAPI process. No new process. Lower complexity, shares process memory, suitable if gateway is lightweight.
- **Model B — Standalone Supervisord process** on port 8001, separate FastAPI app, separate process boundary. Better fault isolation, independent restart, suitable if gateway handles significant load or requires independent scaling.

State the recommendation clearly. Do not leave this ambiguous. The rest of the implementation depends on this choice.

---

#### DIMENSION F — Migration Risk Analysis

**Breaking changes**
- Every agent file requiring refactoring — file and line
- Every test that would break due to changed call paths
- Every environment variable that would change name or value

**Backward compatibility**
- Whether the existing direct-MCP path can remain active during migration as a parallel path or feature flag
- The earliest point at which the old path must be removed

**Downtime risk**
- Whether the gateway can be introduced without restarting the FastAPI process
- Whether Supervisord can reload individual processes without full container restart
- Any database migration requiring table locks or downtime

**Rollback strategy**
- Exact steps to revert from Option 2 back to direct MCP access if the gateway fails
- What must be retained in the codebase to make rollback safe

---

#### DIMENSION G — Performance and Scalability Review

- Current measured or estimated latency per agent tool call — from test output, logs, or OTel traces if present
- Expected latency addition of gateway hop (intra-container TCP: estimate 0.5–2ms; validate against actual setup)
- Whether each agent MCP client is implemented with async/await correctly — file and line; flag any `time.sleep`, `requests.get`, or synchronous `.read()` call in an async context as BLOCKER
- Whether connection pooling exists for database-backed MCP tools — file and line
- Where circuit breakers currently exist versus where they should move to gateway level
- Whether OTel trace context (`traceparent` header) is propagated through MCP calls today
- Whether the gateway introduces any synchronous blocking that would degrade the LangGraph async graph
- **Parallelism opportunity:** Cross-reference with Dimension C parallelism surface. Estimate latency saving if independent agents (e.g. Task Agent and Calendar Agent) were to run concurrently. Record as advisory — do not implement without approval.

---

#### DIMENSION H — Prompt and Security Contract Completeness

For each agent (`task`, `calendar`, `focus`, `critic`, `orchestrator`, `security`) confirm:
- `CONTRACT.md`, `guardrails.md`, `system.md`, `CHANGELOG.md` — file paths or MISSING
- `prompt_version` in `AgentResultEnvelope` enforced in code — file and line
- Security prompt contract in `prompts/security/` referenced by Critic Agent implementation

---

#### DIMENSION I — Existing Jira Coverage and Sequencing

- Every existing epic: ID, title, status (complete / in progress / planned)
- Every task overlapping with Option 2 MCP Gateway work — superseded or extended
- Every task conflicting with Option 2 — must be revised or deprecated
- Highest existing task ID — for new ID sequencing
- Critical path: which existing tasks must be complete before gateway work begins
- **Parallelisable work packages:** From critical path analysis, identify which Phase 3 work packages have no dependency on each other and can be assigned to separate agents or developers concurrently. List these explicitly.

---

#### DIMENSION J — MCP Tool Schema Compatibility Audit

This is one of the highest-risk implementation areas. For every MCP tool call in the system:

**Agents → Gateway compatibility**

Compare each agent's current outbound call shape against the `GatewayToolRequest` contract defined at the top of this prompt:
- What request payload shape does each agent currently send when calling an MCP tool — file and line
- What response payload shape does each agent expect back — file and line
- Does the agent call currently include `trace_id`, `agent_id`, and `mcp_protocol_version` fields, or must these be added in the refactor

**Gateway → MCP server compatibility**
- What tool schemas are defined in `docs/MCP.md` for each MCP server
- What tool schemas are actually implemented in the MCP server integration code — file and line
- What MCP protocol version does each registered server declare — cross-reference Dimension A MCP version audit
- Are there any mismatches between documented schemas and implementation
- Are there any mismatches between declared MCP protocol versions — flag as BLOCKER if mismatch exists

**Pydantic model coverage**
- Are request and response payloads modelled as Pydantic v2 types or as raw dicts — file and line
- Are there any unvalidated dict payloads that must be typed before the gateway can route them safely

**Compatibility matrix:**

```
| Tool              | Agent Sends (type) | Agent Expects (type) | MCP Accepts (type) | MCP Returns (type) | MCP Version        | Compatible       |
|---|---|---|---|---|---|---|
| pg_query          | ?                  | ?                    | ?                  | ?                  | ?                  | YES/NO/PARTIAL   |
| pg_list_tables    | ?                  | ?                    | ?                  | ?                  | ?                  |                  |
| calendar_get_events | ?                | ?                    | ?                  | ?                  | ?                  |                  |
| injection_scan    | ?                  | ?                    | N/A (new)          | N/A (new)          | N/A (new)          | N/A              |
```

Flag any incompatibility as a BLOCKER. Flag any MCP protocol version mismatch as a BLOCKER.

---

#### DIMENSION K — Data Flow Inventory

Trace every data flow through the system for a single briefing request. This is required for security and observability design.

```
1. User request
   [Browser → Next.js → FastAPI: what fields, what headers, what JWT claims]

2. JWT propagation
   [FastAPI → LangGraph → Agent: where does the JWT travel, where does it stop]

3. Agent tool call
   [Agent → MCP call: what payload, what credentials, what trace context]

4. MCP server response
   [MCP server → Agent: what payload shape, what metadata]

5. AgentResultEnvelope assembly
   [Agent → Orchestrator: what fields are populated, what is dropped]

6. Database write path
   [Orchestrator/FastAPI → SQLAlchemy → Supabase: what is written, when, by whom]

7. Final response
   [Orchestrator → FastAPI → Next.js: what fields reach the UI]
```

For each step: confirm the data is typed, validated, and sanitised. Flag any step where raw unvalidated data passes a trust boundary.

---

#### DIMENSION L — Failure Mode Analysis

For each failure scenario, document: expected behaviour, current implementation (if any), and required behaviour for Option 2.

| Failure | Expected Behaviour | Currently Implemented | Required for Option 2 |
|---|---|---|---|
| MCP Gateway unavailable | Agents fall back to direct MCP or fail gracefully with DLQ entry | ? | Define behaviour |
| PostgreSQL MCP unavailable | Task Agent fails gracefully, DLQ entry, briefing continues without task data | ? | Circuit breaker at gateway |
| Google Calendar MCP unavailable | Calendar Agent fails gracefully, DLQ entry, briefing continues without calendar data | ? | Circuit breaker at gateway |
| Supabase unavailable | SQLAlchemy writes fail, DLQ unreachable, system logs error and returns partial briefing | ? | Define fallback |
| Partial agent failure | Orchestrator assembles envelope with available results, marks failed agents in escalation field | ? | Confirm envelope handles partial results |
| LLM unavailable | Focus/Critic agents fail, local LLM fallback activated per `docs/LOCAL-LLM.md` | ? | Confirm local fallback wired |
| Injection detected by Critic | Payload scrubbed, escalation reason set, request dropped to DLQ, never retried | ? | Confirm DLQ write path |
| Token budget exceeded | Circuit breaker trips, DLQ entry, no retry | ? | Confirm at gateway level |
| MCP protocol version mismatch | Gateway rejects request, returns `status: "version_mismatch"`, DLQ entry | ? | Required — new for Option 2 |
| Gateway health check failure | Supervisord restarts gateway process; FastAPI returns 503 until gateway recovers | ? | Required — define recovery SLA |

For every row marked `?`: confirm from source evidence whether it is implemented, stubbed, or absent. Flag every absent failure handler as a BLOCKER or MAJOR based on severity.

---

### Step 1.5 — Versioning Determination

Evaluate against audit findings:

- Does Option 2 change the external API contract exposed to Next.js? (Yes/No + evidence)
- Does Option 2 require database schema changes? (Yes/No + evidence)
- Does Option 2 break any existing agent behaviour observable to the end user? (Yes/No + evidence)
- Does Option 2 require environment variable changes that operators must update? (Yes/No + evidence)

Recommend exactly one:
- **v2.0.0** — breaking architectural change affecting operators or consumers
- **v1.6.0** — internal refactor, no breaking external changes
- **v1.5.1** — purely additive, zero breaking changes

---

### Phase 1 Output — Audit Report

```
## AUDIT REPORT — Option 2 MCP Gateway Readiness
## Prompt Version: 4.0.0
## Generated: [date]
## Codebase State: [git commit hash or "unavailable"]
## Discovery Method: [shell commands / file indexing / partial — specify]
## Phase 1 Time Used: [minutes]

### ARCHITECTURE COMPARISON
[Current state reconstructed from source]
[Option 1 summary]
[Option 2 target]
[Comparison summary table — all cells filled]

### DIMENSION A — MCP Implementation Gaps
[file → function → line → finding → severity]
[MCP protocol version findings per server]

### DIMENSION B — Supabase PostgreSQL Gaps
[file → line → finding → severity]

### DIMENSION C — Agent Call Graph
[Reconstructed call graph with file and line references]
[Per-agent gap findings]
[Parallelism surface advisory]

### DIMENSION D — Security Boundary Findings
[Authentication propagation]
[Authorisation checks]
[Secret management]
[Service-to-service trust]
[Outbound network restrictions]

### DIMENSION E — Deployment Impact Assessment
[Per infrastructure file: current state → required change → effort LOW/MEDIUM/HIGH]
[Port 8001 availability: CONFIRMED FREE / CONFLICT — file and line]
[MCP Gateway deployment model recommendation: Model A or Model B with justification]

### DIMENSION F — Migration Risk Analysis
[Breaking changes with file references]
[Backward compatibility assessment]
[Downtime risk: YES/NO with justification]
[Rollback steps — numbered]

### DIMENSION G — Performance and Scalability
[Latency baseline per agent tool call]
[Gateway hop estimate]
[Async correctness findings — BLOCKERs listed separately]
[Circuit breaker placement]
[OTel propagation gaps]
[Parallelism latency saving estimate — advisory]

### DIMENSION H — Prompt Contract Completeness
[Per agent: CONTRACT.md YES/NO | guardrails.md YES/NO | CHANGELOG.md YES/NO]
[prompt_version enforcement evidence]

### DIMENSION I — Jira Coverage Summary
[Existing epics: ID | title | status]
[Superseded tasks]
[Conflicting tasks]
[Highest existing ID: DB-XXX]
[Critical path to gateway work]
[Parallelisable work packages — advisory]

### DIMENSION J — MCP Tool Schema Compatibility Matrix
[Compatibility matrix — all rows filled including MCP Version column]
[BLOCKERs flagged — schema mismatches and version mismatches separately]

### DIMENSION K — Data Flow Inventory
[Per step: typed/validated/sanitised — YES/NO/PARTIAL]
[Trust boundary violations flagged]

### DIMENSION L — Failure Mode Analysis
[Table — all rows completed with evidence]
[BLOCKER failures listed separately]

### VERSIONING RECOMMENDATION
[v?.?.? with justification]

### OPTION 2 GATEWAY READINESS SCORE
[Score 0–10 per dimension A–L with one-line justification]
[Overall readiness: 0–10]
[BLOCKERS list — must be resolved before Phase 3]
[PARALLELISM ADVISORY — agents and work packages that can run concurrently]
```

---

**CONFIRMATION GATE 1**
Stop. Do not proceed to Phase 2 until the user explicitly confirms the audit report. If phase time budget was exceeded, list which dimensions are incomplete and require manual verification before Gate 1 can be cleared.

---

## PHASE 2 — ADR, EFFORT ESTIMATION, AND ARCHITECTURE VALIDATION

---

### Step 2.1 — Architecture Decision Record

Create `docs/adr/ADR-002-mcp-gateway-option2.md`:

```markdown
# ADR-002: Adopt API-First MCP Gateway Architecture (Option 2)

**Status:** Proposed
**Date:** [today]
**Deciders:** [engineering team]
**Supersedes:** N/A
**Related:** [ADR-001 if exists]

## Context

[Describe current state from Phase 1 audit evidence — reference dimensions by letter.
Do not use generic principles. Every sentence must reference an audit finding.]

## Decision Drivers

[Each driver must reference a specific audit finding by dimension and file path.
No generic drivers permitted.]

## Options Considered

### Option 1 — Enterprise Hybrid (Direct MCP per Agent)
**Pros:** [evidence-based, from architecture comparison in Step 1.3]
**Cons:** [evidence-based, from audit dimensions]

### Option 2 — API-First MCP Gateway (Selected)
**Pros:** [evidence-based]
**Cons:** [evidence-based — especially latency from Dimension G]

## Decision

[One paragraph. Reference audit evidence. Reference the deployment model
chosen in Dimension E. Reference the schema compatibility findings from
Dimension J. Reference the MCP protocol version enforcement centralised at
the gateway.]

## Consequences

**Positive:** [each with audit dimension reference]
**Negative / Trade-offs:** [each with audit dimension reference]
**Risks:** [each with Dimension F reference]

## Non-Goals

[Repeat the non-goals from the top of this prompt. Confirm each is respected
by the chosen implementation approach.]

## Implementation Constraints

[Constraints derived from audit findings. Each must be actionable.]

## Rollback Plan

[Exact numbered steps from Dimension F.]

## Success Metrics

The following measurable criteria define successful delivery of Option 2:

| Metric | Target | Measurement Method |
|---|---|---|
| Gateway p95 latency (excl. LLM) | ≤ 200ms | OTel trace percentile |
| Security boundary count | 1 central (down from N per agent) | Architecture review |
| OTel span coverage | 100% of MCP tool calls traced | OTel collector query |
| Unit test coverage — gateway | ≥ 80% | pytest coverage report |
| Integration test coverage | All agent → gateway → MCP paths | Test run |
| Zero regressions | All existing tests pass | CI pipeline |
| Failure modes handled | 100% of Dimension L rows | Manual review |
| MCP protocol version enforcement | 100% of tool calls validated | Gateway log query |
| Gateway health check recovery | ≤ 30s from crash to healthy | Supervisord restart test |

## Review Date

[End of the MVP sprint in which Option 2 is delivered, per critical path
from Dimension I.]
```

---

### Step 2.2 — Effort Estimation and Critical Path

Produce an effort estimation table. Use these definitions:
- **S** = 1–2 days (1–2 story points)
- **M** = 3–5 days (3–5 story points)
- **L** = 6–10 days (8 story points)
- **XL** = 10+ days (13 story points)

Do not calculate calendar duration automatically. Leave the duration field blank and note: "Duration depends on team velocity. Fill in based on your actual sprint capacity before committing."

```
## EFFORT ESTIMATION — Option 2 Implementation

| # | Work Package | Depends On | Effort | Points | Risk | Parallelisable With | Notes |
|---|---|---|---|---|---|---|---|
| 1 | MCP Gateway skeleton ([Model A or B — from Dimension E]) | — | | | | — | |
| 2 | Tool registry | 1 | | | | — | |
| 3 | Request routing + GatewayToolRequest/Response schema enforcement | 2 | | | | — | |
| 4 | Gateway auth boundary | 3 | | | | — | |
| 5 | SSRF defence migration | 4 | | | | — | |
| 6 | Injection scan endpoint | 1 | | | | — | |
| 7 | OTel span instrumentation | 1 | | | | 6 | Can run alongside #6 |
| 8 | Circuit breakers | 1 | | | | 6,7 | Can run alongside #6 and #7 |
| 9 | Failure mode handlers (from Dimension L BLOCKERs) | 1,8 | | | | — | |
| 10 | Schema compatibility fixes (from Dimension J BLOCKERs) | 3 | | | | — | |
| 11 | Task Agent refactor | 3,10 | | | | 12 | Independent of Calendar Agent |
| 12 | Calendar Agent refactor | 3,10 | | | | 11 | Independent of Task Agent |
| 13 | Critic Agent refactor | 6,10 | | | | — | |
| 14 | Supabase connection swap | — | | | | 1 | Can start in parallel with gateway skeleton |
| 15 | pgvector migration | 14 | | | | — | |
| 16 | RLS policies | 14 | | | | 15 | Can run alongside #15 |
| 17 | Alembic migration update | 14 | | | | — | |
| 18 | AgentResultEnvelope update (gateway_trace_id) | 11,12,13 | | | | — | |
| 19 | Prompt contract updates (if required by audit) | 11,12,13 | | | | — | |
| 20 | Docker Compose / Supervisord update | 1 | | | | 14 | |
| 21 | CI/CD update | 20 | | | | — | |
| 22 | Unit tests — gateway | 1–10 | | | | — | |
| 23 | Integration tests | all above | | | | — | |
| 24 | Documentation updates | all above | | | | 25 | Can run alongside #25 |
| 25 | ADR finalisation | all above | | | | 24 | |

TOTAL ESTIMATED POINTS: [sum]
CRITICAL PATH: [ordered list of blocking dependencies by work package number]
PARALLELISABLE GROUPS: [list groups of work packages that can run concurrently, e.g. {11,12}, {6,7,8}, {14,20}]
CALENDAR DURATION: [leave blank — fill based on team velocity before committing]
BLOCKERS FROM AUDIT: [list any BLOCKER findings that must be resolved before work begins]
```

---

**CONFIRMATION GATE 2**
Stop. Do not proceed to Gate 2.5 until the user explicitly confirms the ADR and effort estimates.

---

### Step 2.3 — Architecture Validation (Gate 2.5)

Before generating any implementation tasks or modifying any file, validate the proposed gateway design against the audit findings. Answer every question with evidence.

**Deployment model validation**
- Is the deployment model recommended in Dimension E (Model A or Model B) consistent with the Supervisord process count, Docker image structure, and CI/CD pipeline found in the audit?
- Is port 8001 confirmed free per the port binding audit in Step 1.1?
- Does the recommended model conflict with any ENGINEERING-STANDARDS.md constraint?

**Schema contract validation**
- Do all BLOCKER-level schema incompatibilities from Dimension J have corresponding work packages in Step 2.2?
- Is the `GatewayToolRequest` / `GatewayToolResponse` contract from the top of this prompt structurally compatible with every agent's current payload shape, after applying the refactor work packages?
- Is `mcp_protocol_version` propagated correctly through every tool call path in the proposed implementation?

**Security boundary validation**
- Does the proposed gateway centralise all SSRF defences without leaving any direct agent-to-MCP path unguarded?
- Does JWT propagation reach the gateway auth boundary correctly given the current FastAPI auth implementation?

**Failure mode validation**
- Does the proposed implementation handle every BLOCKER failure mode from Dimension L, including the two new rows added in this version (MCP protocol version mismatch, gateway health check failure)?
- Is the DLQ write path available to the gateway, or does it require a new dependency?

**Non-goals validation**
- Confirm each non-goal is unaffected by the proposed implementation:
  - Next.js API contract: [SAFE / AT RISK — evidence]
  - Agent prompt content: [SAFE / AT RISK — evidence]
  - Business logic: [SAFE / AT RISK — evidence]
  - User-facing behaviour: [SAFE / AT RISK — evidence]
  - Existing passing tests: [SAFE / AT RISK — evidence]

If any item is AT RISK, stop and flag it. Do not proceed until the user approves the risk or the design is adjusted.

**Gate 2.5 Output:**

```
## ARCHITECTURE VALIDATION REPORT

### Deployment Model: [Model A / Model B] — CONFIRMED / CONFLICTS FOUND
[Evidence]

### Port 8001: FREE / CONFLICT
[Evidence from Step 1.1 port binding audit]

### Schema Contract: CLEAR / BLOCKERS REMAIN
[Evidence — reference GatewayToolRequest/Response contract compliance]

### MCP Protocol Version Enforcement: CONFIRMED / GAPS FOUND
[Evidence]

### Security Boundary: COMPLETE / GAPS FOUND
[Evidence]

### Failure Mode Coverage: COMPLETE / GAPS FOUND
[Evidence — confirm new rows for version mismatch and health check recovery]

### Non-Goals: ALL SAFE / [list AT RISK items]
[Evidence]

### VERDICT: PROCEED TO PHASE 3 / HOLD — [reason]
```

---

**CONFIRMATION GATE 2.5**
Stop. Do not proceed to Phase 3 until the user explicitly confirms the architecture validation report and the verdict is PROCEED.

---

## PHASE 3 — FULL IMPLEMENTATION PLAN (AFTER GATE 2.5 CONFIRMATION)

---

### Step 3.1 — Pre-Implementation Schema Contract Checkpoint

Before writing any implementation code, verify the following in the existing codebase. This checkpoint must pass before the Coding Agent begins work on any file.

```
SCHEMA CONTRACT CHECKPOINT

1. GatewayToolRequest and GatewayToolResponse models exist at:
   backend/mcp_gateway/schemas/contract.py — PRESENT / ABSENT

2. Every agent that calls the gateway imports GatewayToolRequest and
   constructs it with all required fields (tool, mcp_server, payload,
   trace_id, agent_id, mcp_protocol_version) — CONFIRMED / GAPS: [list files]

3. Every agent that receives a gateway response parses it as
   GatewayToolResponse — no raw dict access — CONFIRMED / GAPS: [list files]

4. mcp_protocol_version "2025-03-26" is defined as a constant in
   backend/mcp_gateway/schemas/contract.py and imported by agents
   — CONFIRMED / ABSENT

5. No raw dict crosses the gateway boundary in any file under backend/ — 
   CONFIRMED / VIOLATIONS: [list files and lines]
```

If any item is ABSENT or lists violations, the Coding Agent must resolve it before implementing any other work package. These are pre-conditions, not concurrent tasks.

---

### Step 3.2 — Update Project Proposal

Update `007-01-ai-daily-briefing-assistant5.md` as follows:

- Apply the version determined in Step 1.5 — do not default to v2.0.0
- Add a changelog entry at the top: date, version, summary of architectural change to Option 2, reference to ADR-002
- Update the architecture description to reflect the confirmed MCP Gateway topology from Gate 2.5
- Update the MVP delivery table — insert MCP Gateway as a discrete milestone at the sprint position confirmed by the critical path in Step 2.2
- Update the agent role framework table — add a `Gateway Route` column
- Update the MCP integrations table — add `Gateway Endpoint` and `MCP Protocol Version` columns
- Update the Docker development architecture section to show the confirmed deployment model (Model A or B)
- Update the project tree to include `backend/mcp_gateway/` with the structure below — adjust for Model A or B as appropriate:

```
backend/mcp_gateway/
├── AGENT.md
├── main.py              # Gateway app entry point
├── registry.py          # Tool registry — MCP server registration with version declarations
├── router.py            # Inbound tool call routing
├── auth.py              # Agent identity validation
├── ssrf.py              # SSRF defence — allowlist enforcement
├── scan.py              # Injection scan endpoint for Critic Agent
├── telemetry.py         # OTel span instrumentation
├── circuit_breaker.py   # Per-MCP-server circuit breaker
├── failure_handlers.py  # Failure mode handlers from Dimension L
├── version_guard.py     # MCP protocol version enforcement and drift detection
├── schemas/
│   ├── contract.py      # GatewayToolRequest and GatewayToolResponse — canonical wire format
│   ├── requests.py      # Pydantic v2 request models per tool
│   └── responses.py     # Pydantic v2 response models per tool
└── tests/
    ├── test_routing.py
    ├── test_auth.py
    ├── test_ssrf.py
    ├── test_schemas.py
    ├── test_version_guard.py
    └── test_integration.py
```

- Do not remove existing OWASP GenAI security content — extend it to cover gateway-level controls
- British English throughout, no contractions, no hyphens in compound modifiers

---

### Step 3.3 — Generate Jira Tasks

Create new epic and task JSON files in `docs/jira-tickets-json/`. Use the exact JSON schema of existing files. All new IDs continue from the highest ID confirmed in Dimension I. Story points must match Step 2.2 estimates exactly.

Generate tasks for the following epics using the work packages from Step 2.2:

**Epic: MCP Gateway Service** — all work packages 1–10 and 22–23 from Step 2.2

**Epic: Supabase PostgreSQL Migration** — work packages 14–17

**Epic: Agent Refactor — Gateway Integration** — work packages 11–13, 18–19

**Epic: Observability — Gateway Tracing** — OTel collector config, per-agent per-tool dashboard panels, SLO definition (p95 ≤ 200ms excluding LLM), circuit breaker alert rule, MCP protocol version drift alert rule

**Epic: Documentation and ADR** — work packages 24–25

Each task JSON must include: `id`, `type`, `summary`, `description`, `acceptance_criteria` (minimum three per task), `story_points`, `labels`, `epic_link`, `dependencies`, `estimated_effort`, `parallelisable_with` (list of task IDs that can run concurrently), `non_goals_check` (confirm which non-goals this task does not affect).

---

### Step 3.4 — Autonomous Workflow Execution

After all documents and Jira files are updated, begin implementation in critical path order from Step 2.2. Execute parallelisable work packages concurrently where Cursor Agent mode supports it, using the parallelisable groups identified in Step 2.2.

```
For each epic:

1. git checkout epic/autonomus-implementation && git pull
2. git checkout -b epic/E[N]-[epic-slug]
3. Schema Contract Checkpoint (Step 3.1) — must pass before Coding Agent writes any code
4. Coding Agent    → implement all tasks in critical path order; run parallelisable groups concurrently
5. Refactor Agent  → code quality, schema validation, sanitisation
6. Testing Agent   → add tests, verify coverage meets ADR success metrics
7. Docs Agent      → update AGENT.md files, ARCHITECTURE.md, OTel docs
8. CI must pass before merge
9. git merge commit → epic/autonomus-implementation (no squash, no rebase)
10. Delete local epic branch, keep remote
```

**Context management:** At 75% context usage, write checkpoint to `docs/tasks/checkpoint.md` and stop.

**Standards:**
- British English in all documentation, no contractions, no hyphens in compound modifiers
- All new code async-first (FastAPI, SQLAlchemy 2.x, LangGraph) — no `time.sleep`, no synchronous `requests` calls in async context
- All new code typed with Pydantic v2 models — no raw dicts at trust boundaries; `GatewayToolRequest` and `GatewayToolResponse` are the mandatory wire types
- All secrets from environment variables only — never hardcoded
- OTel `traceparent` header propagated through every gateway call; `mcp_protocol_version` echoed in every `GatewayToolResponse`
- Do not modify existing passing tests — only add new ones
- Do not touch Next.js API contract, agent prompt content, business logic, or user-facing behaviour unless a specific audit finding requires it and the user has approved it at a gate

---

*Prompt Version: 4.0.0 — Option 2 API-First MCP Gateway — May 2026*
