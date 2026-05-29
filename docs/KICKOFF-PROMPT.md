# Kick-off Prompt — AI Daily Briefing Assistant

**Version:** 1.6.0 | **Last Updated:** May 2026

This document contains the ready-to-use prompt to start autonomous implementation of the AI Daily Briefing Assistant.

---

## Pre-Flight Checklist

Before running the kick-off prompt, verify:

- [ ] All documentation files are present in `daily-briefing/`
- [ ] `docs/jira-tickets-json/` contains 6 epic JSON files (DB-E1 through DB-E6)
- [ ] `docs/tasks/todo.md` exists and is ready for updates
- [ ] `docs/tasks/lessons.md` exists with initial structure
- [ ] `docs/tasks/checkpoint.md` exists for context handoff
- [ ] `.cursor/rules/` contains all 4 rule files (coding, testing, refactor, docs)
- [ ] Git repository is initialized (if implementing in new location)

---

## Kick-off Prompt (Copy This)

```
You are implementing the AI Daily Briefing Assistant project from scratch.

## CRITICAL: Read These Files First (In Order)
1. AGENT.md — Root index with workflow rules
2. docs/EXECUTION-RULES.md — Execution discipline and context management
3. docs/tasks/checkpoint.md — Current state (starting fresh)
4. docs/PLAN.md — Implementation progress tracker
5. .cursor/rules/* — All cursor rules for coding, testing, refactor, and docs

## Project Overview
- Multi-agent orchestration system using LangGraph
- Single Docker container deployment (FastAPI + Next.js + Nginx)
- MCP integrations for PostgreSQL and Google Calendar
- OWASP GenAI security hardening

## Your Mission
Implement Epic DB-E1 (MVP 1: Project Scaffold) following the autonomous workflow:

### Workflow
0. Run environment checks: Verify uv, npm, docker, and python versions. Fail fast if missing.
1. Create branch: `git checkout -b epic/E1-project-scaffold`
2. Read all tasks from `docs/jira-tickets-json/DB-E1-mvp1-scaffold.json`
3. Update `docs/tasks/todo.md` with your implementation plan
4. Implement each task following IMPLEMENTATION DETAILS and EDGE CASES. Check existing code first to avoid duplicating/overwriting logic.
5. After coding: run Refactor Agent checks
6. After refactor: run Testing Agent checks and VERIFY the test suite passes (0 failures)
7. After testing: run Docs Agent updates
8. Update `docs/PLAN.md` with completion status
9. Commit and prepare PR to `epic/autonomus-implementation`

### Context Management
- At ~75% context usage, write checkpoint to `docs/tasks/checkpoint.md`
- Commit WIP and document next steps
- New session will continue from checkpoint

### Rules
- Always use a `<thought>` or `<scratchpad>` block to plan your file modifications before writing code.
- If you encounter the same error 3 times, STOP. Document the blocker in docs/tasks/checkpoint.md and ask the user for guidance.
- Every LangGraph node returns AgentResultEnvelope
- All external inputs are untrusted (prompt injection defense)
- Only Orchestrator produces user-facing markdown
- Use `uv` for Python, `npm` for Node.js
- Pydantic v2 with strict=True for all schemas
- structlog for JSON logging with trace_id

## Start Now
Begin with DB-001: Monorepo Init with Root AGENT.md
Read the task details from `docs/jira-tickets-json/DB-E1-mvp1-scaffold.json`
```

---

## Session Continuation Prompt

Use this prompt when resuming from a checkpoint:

```
Continue implementing the AI Daily Briefing Assistant.

## CRITICAL: Read These Files First
1. docs/tasks/checkpoint.md — Resume from this state
2. docs/tasks/lessons.md — Any learnings from previous session
3. docs/PLAN.md — Current progress

## Current State
[The checkpoint.md file contains the exact state - read it first]

## Rules Reminder
- Follow docs/EXECUTION-RULES.md for all workflow rules
- Update checkpoint.md at 75% context usage
- Commit progress before session end
- Always use a `<thought>` block to plan modifications
- Check existing state before overwriting
- Stop and ask for help if stuck on the same error 3 times

## Continue
Resume from the task and step documented in checkpoint.md.
```

---

## Epic-Specific Prompts

### MVP 1: Project Scaffold (DB-E1)
```
Implement Epic DB-E1: Project Scaffold
Branch: epic/E1-project-scaffold
Tasks: DB-001 through DB-010
Focus: Docker, FastAPI, Next.js, LangGraph scaffold, CI pipeline
```

### MVP 2: Core Agents (DB-E2)
```
Implement Epic DB-E2: Core Agents
Branch: epic/E2-core-agents
Tasks: DB-011 through DB-020
Focus: MCP clients, Task/Calendar/Focus agents, LLM router, prompts
```

### MVP 3: Observability (DB-E3)
```
Implement Epic DB-E3: Observability
Branch: epic/E3-observability
Tasks: DB-021 through DB-028
Focus: Critic agent, DLQ, OpenTelemetry, Prometheus, logging, frontend components
```

### MVP 4: Agentic Consent (DB-E4)
```
Implement Epic DB-E4: Agentic Consent
Branch: epic/E4-agentic-consent
Tasks: DB-029 through DB-036
Focus: Consent model, JIT auth, local LLM fallback, preferences, export
```

### MVP 5: Security Hardening (DB-E5)
```
Implement Epic DB-E5: Security Hardening
Branch: epic/E5-security-hardening
Tasks: DB-037 through DB-044
Focus: OWASP audit, sanitization, circuit breakers, rate limiting, security tests
```

### MVP 6: Production Deployment (DB-E6)
```
Implement Epic DB-E6: Production Deployment
Branch: epic/E6-production
Tasks: DB-045 through DB-052
Focus: Docker signing, health checks, graceful shutdown, SLOs, alerts, E2E tests
```

---

## Expected First Session Output

By end of first session (or checkpoint), you should have:

1. **Branch created:** `epic/E1-project-scaffold`
2. **Files created:**
   - `pyproject.toml` with uv dependencies
   - `.env.example` with all env vars
   - `.gitignore`
   - `README.md`
   - `Dockerfile` (multi-stage)
   - `nginx.conf`
   - `supervisord.conf`
   - `docker-compose.yml`
   - `backend/main.py`, `backend/settings.py`
   - `frontend/` Next.js scaffold
   - `backend/graph/` LangGraph scaffold
   - `backend/schemas/envelope.py`
   - `.github/workflows/ci.yml`
3. **Documentation updated:**
   - `docs/tasks/todo.md` with progress
   - `docs/PLAN.md` with DB-E1 status
4. **Tests passing:** Basic CI pipeline green

---

## Troubleshooting

### "I don't have access to the files"
Ensure all files from `daily-briefing/` are in the working directory.

### "Context is getting long"
Write checkpoint immediately, commit WIP, document next steps clearly.

### "Task is unclear"
Check the IMPLEMENTATION DETAILS and EDGE CASES in the JSON file. If still unclear, make a reasonable decision and document it in `docs/adr/`.

### "Tests are failing"
Fix before proceeding. Never move to next task with failing tests.

---

*Kick-off Prompt — Version 1.6.0 — May 2026*
