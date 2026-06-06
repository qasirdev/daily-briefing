# AGENT.md — AI Daily Briefing Assistant

## What this file is

This is the root index for the AI Daily Briefing Assistant.
All engineering standards, agent specs, and prompt rules live in
co-located AGENT.md files alongside the code they govern.

**Architecture:** Multi-Agent Orchestration | MCP Servers (stdio) | Supabase | Cursor Development Agents  
**Deployment:** Single Docker Container (Option 1 Enterprise Hybrid)  
**Version:** 1.6.0 | May 2026

> **Option 1 implemented:** stdio MCP (`@modelcontextprotocol/server-postgres`, `@franciscpd/calendar-mcp-server`), Supabase persistence (Alembic/SQLAlchemy), Docker on **8088**. Setup: [docs/guidence/docker-setup.md](docs/guidence/docker-setup.md).

---

## Workflow Rules (read at every session start)

| Rule | Behaviour |
|---|---|
| Token usage | Follow `docs/TOKEN-EFFICIENCY.md` — read before `docs/KICKOFF-PROMPT.md` |
| Plan mode | Required for any epic/task or task with 3+ steps — check `docs/jira-tickets-json/*.json` |
| Edge cases | Review the `Description` field in `docs/jira-tickets-json/*.json` — implement every item under `EDGE CASES` (DB-E2 format: `IMPLEMENTATION DETAILS`, `TESTING CRITERIA`, `EDGE CASES` sections per task) |
| Task log | Write plan to `docs/tasks/todo.md` before any implementation |
| Verify plan | Check in before starting — do not build on an unconfirmed plan |
| Subagents | Offload research, exploration, parallel analysis to subagents |
| Lessons review | Read `docs/tasks/lessons.md` at session start before touching code |
| Correction loop | After any user correction: update `docs/tasks/lessons.md` immediately |
| Done gate | Never mark complete without proving it works (tests, logs, diff) |
| Backend verification gate | Before marking any backend task done, run: `uv run ruff check backend && uv run ruff format backend && uv run mypy backend && uv run pytest` (see `backend/AGENT.md`) |
| Elegance check | For non-trivial changes: pause and ask "is there a more elegant way?" |
| Bug reports | Fix autonomously — point at logs/errors and resolve without hand-holding |
| Security First | Check `docs/SECURITY.md` before modifying agent inputs/outputs |
| Local LLM | Respect `docs/LOCAL-LLM.md` fallback rules for privacy-sensitive tasks |
| Agent Envelope | All agents MUST return `AgentResultEnvelope` (see `backend/schemas/`) |
| DLQ Handling | Failed agents or unrecoverable MCP timeouts MUST route to the DLQ |
| Orchestrator-as-Presenter | Only the Orchestrator synthesizes user-facing markdown; sub-agents return JSON |
| JIT Consent | Never hardcode credentials; respect Agentic Consent for Google Calendar MCP |
| Prompt creation | New agents in `prompts/` require all 11 files following v2.0.0 standards: system.md, context.md, instructions.md, examples.md, output-schema.md, tools.md, reasoning.md, guardrails.md, quality-checklist.md, CHANGELOG.md, CONTRACT.md (see `prompts/AGENT.md` and `prompts/focus/` for structure) |
| Prompt caching | Structure prompts for caching: static content (system, examples) before dynamic (user input), >1024 tokens for OpenAI auto-cache, use Claude's cache_control markers |
| Agent creation | New agents in `backend/agents/` require a co-located `AGENT.md` |
| Knowledge capture | New techniques or non-trivial fixes go in `docs/learning/` |
| Task tracking | Update `docs/tasks/todo.md` and `docs/tasks/lessons.md` on completion |
| Reference standards | Consult `docs/example-code/` before writing new code |
| Clean up | Delete temporary scripts from the root at task completion |
| Json Sync | JSON ticket changes MUST update `docs/PLAN.md` |
| Context checkpoint | At ~75% context, write `docs/tasks/checkpoint.md` and commit WIP |

---

## MVP Delivery Overview

| Milestone | Scope Summary | Status |
|---|---|---|
| **MVP 1** | Next.js UI scaffold, FastAPI backend, LangGraph orchestration, basic MCP integration | ✅ Done |
| **MVP 2** | PostgreSQL MCP, Task Agent, Calendar Agent, Focus Agent implementation | ✅ Done |
| **MVP 3** | Critic Agent, DLQ routing, observability baseline, OpenTelemetry integration | ✅ Done |
| **MVP 4** | Agentic Consent modal, Local LLM fallback, learner feedback loops | ✅ Done |
| **MVP 5** | Comprehensive OWASP GenAI Security Hardening, Prompt Injection Defense | ✅ Done |
| **MVP 6** | Orchestrator-as-Presenter finalization, production deployment, Docker signing | ✅ Done |
| **Option 1** | Supabase + stdio MCP + Alembic + Docker E2E (DB-E7, DB-053–057) | ✅ Done |

---

## Where to look

| Concern | File | MVP |
|---|---|---|
| Architecture & agent roles | docs/ARCHITECTURE.md | MVP 1 |
| Model Context Protocol (MCP) | docs/MCP.md | MVP 2 |
| **Run locally / Docker** | docs/guidence/try-it-locally.md, docs/guidence/docker-setup.md | Option 1 |
| **Supabase setup** | docs/guidence/supabase-setup.md | Option 1 |
| **Google Calendar OAuth** | docs/guidence/google-calandar-setup.md | Option 1 |
| Engineering Standards (FE/BE/DB) | docs/ENGINEERING-STANDARDS.md | MVP 1 |
| Details of epics and tasks | docs/jira-tickets-json/*.json (DB-E2 `Description` format — see `docs/jira-tickets-json/README.md`) | MVP 1–6, Gap Weeks 1–8 |
| Observability & Tracing | docs/OBSERVABILITY.md | MVP 3 |
| Data Ownership & Learner Loops | docs/DATA-OWNERSHIP.md | MVP 4 |
| Agentic Consent | docs/AGENTIC-CONSENT.md | MVP 4 |
| Local LLM Fallback | docs/LOCAL-LLM.md | MVP 4 |
| Security & OWASP GenAI | docs/SECURITY.md | MVP 5 |
| Final execution rules | docs/EXECUTION-RULES.md | MVP 1 |
| Implementation progress | docs/PLAN.md | MVP 1 |
| Token efficiency (context window) | docs/TOKEN-EFFICIENCY.md | MVP 1 |
| Kick-off prompt | docs/KICKOFF-PROMPT.md | MVP 1 |
| Context checkpoint | docs/tasks/checkpoint.md | MVP 1 |
| Active task plan | docs/tasks/todo.md | MVP 1 |
| Self-improvement log | docs/tasks/lessons.md | MVP 1 |
| Knowledge capture | docs/learning/ | MVP 1 |
| Architectural decisions | docs/adr/ | MVP 1 |
| Reference implementations | docs/example-code/ | MVP 1 |
| Frontend Rules | frontend/AGENT.md | MVP 1 |
| Backend & LangGraph Rules | backend/AGENT.md | MVP 1 |
| Prompt Versioning & Contracts | prompts/AGENT.md | MVP 1 |
| CI/CD & Infrastructure | infrastructure/AGENT.md | MVP 1 |
| Docker multi-stage build | Dockerfile, nginx.conf, supervisord.conf | MVP 1 |

Per-agent `AGENT.md` files (Task, Calendar, Focus, Critic, Orchestrator, Security) are created during MVP 2–5 — see `backend/AGENT.md` for the directory layout.

---

## Agent Communication Protocol

All inter-agent communication uses `AgentResultEnvelope`. Full schema, field validators, and examples: `backend/schemas/envelope.py`, `docs/ARCHITECTURE.md`, and `backend/AGENT.md`.

---

## Cursor Development Agents

| Cursor Agent | Scope | Rules File | Order |
|---|---|---|---|
| **Coding Agent** | Endpoints, LangGraph, prompt injection defense | `.cursor/rules/coding.mdc` | 1st |
| **Refactor Agent** | Schema validation, output sanitization | `.cursor/rules/refactor.mdc` | 2nd |
| **Testing Agent** | OWASP GenAI boundary tests | `.cursor/rules/testing.mdc` | 3rd |
| **Documentation Agent** | Domain `AGENT.md` and OWASP checklists | `.cursor/rules/docs.mdc` | 4th |

Epic workflow: branch → implement → refactor → test → docs → PR to `epic/autonomus-implementation` → **merge commit** → delete local epic branch (keep remote). Details in `.cursor/rules/coding.mdc` and `docs/EXECUTION-RULES.md` §9.

---

*AI Daily Briefing Assistant — Version 1.6.0 — May 2026*
