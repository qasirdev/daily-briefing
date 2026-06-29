# Multi-Agent Rules — AI Daily Briefing Assistant

**Version:** 1.6.0 | **Last Updated:** June 2026

---

## Scope

This file indexes all LangGraph domain agents. Kernel graph nodes (`input_security_gate`, `consensus_evaluator`, `dlq_handler`) are documented in `backend/graph/AGENT.md`.

---

## Agent Index

| Agent | Role | Module | AGENT.md |
|---|---|---|---|
| Task | Doer | `backend/agents/task/` | `task/AGENT.md` |
| Calendar | Tool Operator | `backend/agents/calendar/` | `calendar/AGENT.md` |
| Focus | Planner | `backend/agents/focus/` | `focus/AGENT.md` |
| Verification | Verifier | `backend/agents/verification/` | `verification/AGENT.md` |
| Adversarial | Red Team | `backend/agents/adversarial/` | `adversarial/AGENT.md` |
| Critic | Safety + Quality | `backend/agents/critic/` | `critic/AGENT.md` |
| Consensus | Evaluator (deterministic) | `backend/agents/consensus/` | `consensus/AGENT.md` |
| Orchestrator | Supervisor + Presenter | `backend/agents/orchestrator/` | `orchestrator/AGENT.md` |

---

## Pipeline (when `enable_consensus_workflow=True`)

```
Orchestrator route
  → Task ∥ Calendar (parallel MCP)
  → Input security gate
  → Focus
  → Verification → Adversarial → Critic
  → Consensus evaluator
  → Orchestrator present
```

Escalations (`max_retries_exceeded`, `mcp_timeout`, `security_violation_detected`, `token_budget_exceeded`) route to `dlq_handler` per `backend/graph/builder.py`.

---

## Universal Rules

| Rule | Behaviour |
|---|---|
| Envelope protocol | Every domain agent node returns `AgentResultEnvelope` stored on `BriefingGraphState` |
| Orchestrator-as-Presenter | Only `orchestrator_present` synthesizes user-facing markdown |
| Critic safety | `security_violation_detected` → DLQ, never retried |
| Revision cap | Critic allows at most 2 revision cycles |
| Verification / Adversarial | 1 retry each (`verification_failed`, `adversarial_concerns`); exhausted retries → DLQ (`max_retries_exceeded`) |

---

*See also:* `backend/AGENT.md` · `docs/ARCHITECTURE.md` · `007-01-ai-daily-briefing-assistant-v2.0.0.md`
