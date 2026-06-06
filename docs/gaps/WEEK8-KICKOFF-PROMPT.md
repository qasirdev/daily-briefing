# KICKOFF PROMPT — Week 8: Production Optimization & Agentic RAG

**Epic:** DB-E15 — Week 8 Gap Remediation  
**Integration Branch:** `epic/autonomus-implementation-gap`  
**Feature Branch:** `epic/week8-gap-remediation`  
**Duration:** 5 days (40 hours)

**Scope:** Phase 6 — Agentic RAG, context engineering, reasoning feedback, enumeration detection, deployment gates

---

## Mission

Evolve static memory retrieval into **agentic RAG** (dynamic whether/when/how decisions), apply **context engineering** pillars, complete **reasoning-level feedback**, detect **T1087 enumeration**, and define **deployment gates** on observability metrics.

**Epic Ticket:** `docs/jira-tickets-json/DB-E15-gap-remediation-week8.json`  
**Tasks:** DB-136 (Day 1) through DB-140 (Day 5)

---

## Mandatory Reading

1. `AGENT.md` — workflow rules
2. `docs/tasks/lessons.md` — Week 1–7 learnings
3. `docs/learning/week7-hitl-governance.md`
4. `007-01-ai-daily-briefing-assistant-v2.0.0.md`
5. `docs/gaps/WEEK8-IMPLEMENTATION-GUIDE.md`
6. `docs/MEMORY-ARCHITECTURE.md`

---

## Daily Workflow

| Day | Task | Focus |
|---|---|---|
| 1 | DB-136 | Agentic RAG decision engine |
| 2 | DB-137 | Source validation + context compression |
| 3 | DB-138 | Reasoning-level feedback UI |
| 4 | DB-139 | T1087 enumeration + deployment gates |
| 5 | DB-140 | Integration tests + proof |

**Per-day gate:** `uv run ruff check backend && uv run ruff format backend && uv run mypy backend && uv run pytest`

---

## Success Criteria

- Agentic RAG in `backend/memory/agentic_rag.py`
- `docs/CONTEXT-ENGINEERING.md` complete
- `ReasoningFeedback` component in frontend
- T1087 detected in MITRE registry
- `docs/DEPLOYMENT-GATES.md` complete
- HITL feedback layer implemented
- 420+ tests passing
- `proof/week8/` complete

---

*Week 8 Kickoff — Created 2026-06-06*
