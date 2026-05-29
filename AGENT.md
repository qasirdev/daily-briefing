# AGENT.md — AI Daily Briefing Assistant

## What this file is

This is the root index for the AI Daily Briefing Assistant.
All engineering standards, agent specs, and prompt rules live in
co-located AGENT.md files alongside the code they govern.

**Architecture:** Multi-Agent Orchestration | MCP Servers | Cursor Development Agents  
**Deployment:** Single Docker Container with Advanced Security Posture  
**Version:** 1.5.0 | May 2026

---

## Workflow Rules (read at every session start)

| Rule | Behaviour |
|---|---|
| Plan mode | Required for any epic/task or task with 3+ steps — check `docs/jira-tickets-json/*.json` |
| Edge cases | Review the `Description` field in the relevant JSON and implement associated fail-safes |
| Task log | Write plan to `docs/tasks/todo.md` before any implementation |
| Verify plan | Check in before starting — do not build on an unconfirmed plan |
| Subagents | Offload research, exploration, parallel analysis to subagents |
| Lessons review | Read `docs/tasks/lessons.md` at session start before touching code |
| Correction loop | After any user correction: update `docs/tasks/lessons.md` immediately |
| Done gate | Never mark complete without proving it works (tests, logs, diff) |
| Elegance check | For non-trivial changes: pause and ask "is there a more elegant way?" |
| Bug reports | Fix autonomously — point at logs/errors and resolve without hand-holding |
| Security First | Check `docs/SECURITY.md` before modifying agent inputs/outputs |
| Local LLM | Respect `docs/LOCAL-LLM.md` fallback rules for privacy-sensitive tasks |
| Agent Envelope | All agents MUST return `AgentResultEnvelope` (see `backend/schemas/`) |
| DLQ Handling | Failed agents or unrecoverable MCP timeouts MUST route to the DLQ |
| Orchestrator-as-Presenter | Only the Orchestrator synthesizes user-facing markdown; sub-agents return JSON |
| JIT Consent | Never hardcode credentials; respect Agentic Consent for Google Calendar MCP |
| Prompt creation | New agents in `prompts/` require all 6 files in XML format (see `prompts/AGENT.md`) |
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
| **MVP 1** | Next.js UI scaffold, FastAPI backend, LangGraph orchestration, basic MCP integration | Planned |
| **MVP 2** | PostgreSQL MCP, Task Agent, Calendar Agent, Focus Agent implementation | Planned |
| **MVP 3** | Critic Agent, DLQ routing, observability baseline, OpenTelemetry integration | Planned |
| **MVP 4** | Agentic Consent modal, Local LLM fallback, learner feedback loops | Planned |
| **MVP 5** | Comprehensive OWASP GenAI Security Hardening, Prompt Injection Defense | Planned |
| **MVP 6** | Orchestrator-as-Presenter finalization, production deployment, Docker signing | Planned |

---

## Where to look

| Concern | File | MVP |
|---|---|---|
| Architecture & agent roles | docs/ARCHITECTURE.md | MVP 1 |
| Model Context Protocol (MCP) | docs/MCP.md | MVP 2 |
| Engineering Standards (FE/BE/DB) | docs/ENGINEERING-STANDARDS.md | MVP 1 |
| Details of epics and tasks | docs/jira-tickets-json/*.json | MVP 1–6 |
| Observability & Tracing | docs/OBSERVABILITY.md | MVP 3 |
| Data Ownership & Learner Loops | docs/DATA-OWNERSHIP.md | MVP 4 |
| Agentic Consent | docs/AGENTIC-CONSENT.md | MVP 4 |
| Local LLM Fallback | docs/LOCAL-LLM.md | MVP 4 |
| Security & OWASP GenAI | docs/SECURITY.md | MVP 5 |
| Final execution rules | docs/EXECUTION-RULES.md | MVP 1 |
| Implementation progress | docs/PLAN.md | MVP 1 |
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

All inter-agent communication uses the standardized `AgentResultEnvelope`. See `backend/schemas/envelope.py`, `docs/ARCHITECTURE.md`, and `backend/AGENT.md`.

---

## Cursor Development Agents

| Cursor Agent | Scope | Rules File | Order |
|---|---|---|---|
| **Coding Agent** | Endpoints, LangGraph, prompt injection defense | `.cursor/rules/coding.mdc` | 1st |
| **Refactor Agent** | Schema validation, output sanitization | `.cursor/rules/refactor.mdc` | 2nd |
| **Testing Agent** | OWASP GenAI boundary tests | `.cursor/rules/testing.mdc` | 3rd |
| **Documentation Agent** | Domain `AGENT.md` and OWASP checklists | `.cursor/rules/docs.mdc` | 4th |

Epic workflow: branch → implement → refactor → test → docs → PR to `epic/autonomus-implementation`. Details in `.cursor/rules/coding.mdc`.
---

*AI Daily Briefing Assistant — Version 1.5.0 — May 2026*
