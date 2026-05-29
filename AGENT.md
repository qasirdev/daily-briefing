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
| Plan mode | Required for tasks with 3+ steps, architectural decisions, or any epic/task — check `docs/jira-tickets-json/*.json` for details |
| Edge cases | During implementation, you MUST review the `Description` field in the relevant JSON and implement any associated edge cases or fail-safes |
| Task log | Write plan to `docs/tasks/todo.md` before any implementation |
| Verify plan | Check in before starting — do not build on an unconfirmed plan |
| Subagents | Offload research, exploration, parallel analysis to subagents |
| Lessons review | Read `docs/tasks/lessons.md` at session start before touching code |
| Correction loop | After any user correction: update `docs/tasks/lessons.md` immediately |
| Done gate | Never mark complete without proving it works (tests, logs, diff) |
| Elegance check | For non-trivial changes: pause and ask "is there a more elegant way?" |
| Bug reports | Fix autonomously — point at logs/errors and resolve without hand-holding |
| Security First | Always check `docs/SECURITY.md` for OWASP GenAI and Prompt Injection defense protocols before modifying agent inputs/outputs |
| Local LLM | Respect `docs/LOCAL-LLM.md` fallback rules for privacy-sensitive Doer/Planner tasks |
| Agent Envelope | All agents MUST return the standardized `AgentResultEnvelope` as defined in backend schemas |
| DLQ Handling | Failed agent executions or unrecoverable MCP timeouts MUST be routed to the Dead Letter Queue (DLQ) |
| Orchestrator-as-Presenter | Only the Orchestrator synthesizes final user-facing markdown. Sub-agents return raw JSON |
| JIT Consent | Never hardcode external credentials. Respect Agentic Consent protocols for Google Calendar MCP |
| Prompt creation | When creating a new agent in `prompts/`, you MUST create all 6 files (`CONTRACT.md`, `CHANGELOG.md`, `system.md`, `skills.md`, `tools.md`, `guardrails.md`) adhering to XML format. No exceptions |
| Agent creation | When creating a new agent in `backend/agents/`, you MUST create an `AGENT.md` file in its directory detailing its Role, Input, and Output |
| Knowledge capture | When introducing a new technique, fixing a non-trivial bug, or changing UI patterns, you MUST update or create a `.md` file in `docs/learning/` for future reference |
| Task tracking | Upon completing a requested task, feature, or bug fix, you MUST update `docs/tasks/todo.md` with what was built/changed and log any bugs/resolutions in `docs/tasks/lessons.md` |
| Reference standards | Consult `docs/example-code/` for implementation examples and best practices before writing new code |
| Clean up | Delete all temporary scripts (e.g., test scripts, data patches) from the root directory at the end of task completion |
| Json Sync | Whenever `docs/jira-tickets-json/*.json` files are changed, you MUST automatically update `docs/PLAN.md` to reflect those changes |
| Context checkpoint | At 75% context usage, write checkpoint to `docs/tasks/checkpoint.md` and spawn continuation session with compacted context |

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
| Architecture & Orchestration | docs/ARCHITECTURE.md | MVP 1 |
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
| Backend agent directory layout | backend/AGENT.md | MVP 2–5 |
| Prompt Versioning & Contracts | prompts/AGENT.md | MVP 1 |
| CI/CD & Infrastructure | infrastructure/AGENT.md | MVP 1 |
| Docker multi-stage build | Dockerfile, nginx.conf, supervisord.conf | MVP 1 |

---

## Agent Role Framework

| Agent | Canonical Role | Responsibility | Tools / MCP | Security Posture |
|---|---|---|---|---|
| **Task Agent** | Doer | Reads/prioritises tasks | PostgreSQL MCP | Read-only scope |
| **Calendar Agent** | Tool Operator | Fetches today's events | Google Calendar MCP | Strict Allowlist / SSRF defense |
| **Focus Agent** | Planner | Generates work plan | LLM only | Instruction Hierarchy Enforced |
| **Critic Agent** | Critic (Safety+Quality) | Reviews for coherence and safety violations | LLM only | Acts as final Output Gatekeeper |
| **Orchestrator** | Supervisor + Presenter | Assembles and sanitizes final UI output | — | Composes `AgentResultEnvelope` |

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
| **Documentation Agent** | AGENT.md and OWASP checklists | `.cursor/rules/docs.mdc` | 4th |

---

*AI Daily Briefing Assistant — Version 1.5.0 — May 2026*
