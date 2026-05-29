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
| Plan mode | Required for any task with 3+ steps or architectural decisions |
| Plan mode | Required for any epic/task — check `docs/jira-tickets-json/*.json` for details |
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
| Prompt Versioning & Contracts | prompts/AGENT.md | MVP 1 |
| Task Agent | backend/agents/task/AGENT.md | MVP 2 |
| Calendar Agent | backend/agents/calendar/AGENT.md | MVP 2 |
| Focus Agent | backend/agents/focus/AGENT.md | MVP 2 |
| Critic Agent | backend/agents/critic/AGENT.md | MVP 3 |
| Security Agent | backend/agents/security/AGENT.md | MVP 5 |
| Orchestrator Agent | backend/agents/orchestrator/AGENT.md | MVP 2 |
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

All inter-agent communication follows this envelope schema:

```json
{
  "agent_id": "calendar",
  "canonical_role": "tool_operator",
  "status": "success|failure|escalated",
  "result": { /* agent-specific payload */ },
  "metadata": {
    "execution_ms": 110,
    "tokens_used": 50,
    "model_used": "openai/gpt-4o-mini",
    "prompt_version": "v1.5.0",
    "trace_id": "abc123",
    "data_classification": "confidential_pii"
  },
  "escalation": {
    "reason": "security_violation_detected|max_retries_exceeded|timeout",
    "target_agent": "orchestrator",
    "context": "Additional debugging context"
  }
}
```

---

## Cursor Development Agents

| Cursor Agent | Scope | Rules File | Order |
|---|---|---|---|
| **Coding Agent** | Implements endpoints, LangGraph, and prompt injection defense logic | `.cursor/rules/coding.mdc` | 1st |
| **Refactor Agent** | Tightens schema validation and enforces output sanitization layers | `.cursor/rules/refactor.mdc` | 2nd |
| **Testing Agent** | Enforces OWASP GenAI boundary tests (simulating injection attacks) | `.cursor/rules/testing.mdc` | 3rd |
| **Documentation Agent** | Maintains domain `AGENT.md` and OWASP checklists | `.cursor/rules/docs.mdc` | 4th |

---

## Pre-Flight Checklist

Before starting implementation, verify:

- [ ] Read this file completely (AGENT.md)
- [ ] Read `docs/EXECUTION-RULES.md`
- [ ] Read `docs/tasks/checkpoint.md` for current state
- [ ] Read `docs/tasks/lessons.md` for past learnings
- [ ] Verify epic JSON exists in `docs/jira-tickets-json/`
- [ ] Create epic branch before any code changes

---

## Epic Workflow

For each epic, follow this sequence:

```
1. Create branch: git checkout -b epic/E{n}-{description}
2. Coding Agent: Implement all tasks from JSON
3. Refactor Agent: Review code quality and patterns
4. Testing Agent: Add tests, ensure coverage
5. Docs Agent: Update documentation
6. Merge: PR to main after all checks pass
```

See `.cursor/rules/coding.mdc` for detailed workflow documentation.

---

*AI Daily Briefing Assistant — Version 1.5.0 — May 2026*
