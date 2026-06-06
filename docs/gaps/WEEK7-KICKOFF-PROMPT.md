# KICKOFF PROMPT — Week 7: HITL Layers & Governance Hardening

**Epic:** DB-E14 — Week 7 Gap Remediation  
**Integration Branch:** `epic/autonomus-implementation-gap`  
**Feature Branch:** `epic/week7-gap-remediation`  
**Duration:** 5 days (40 hours)

**Scope:** Phase 5 — Full HITL architecture, per-action authorization, reasoning traces, governance, multi-incident tabletop, emergency change procedures

---

## Mission

Complete the human-in-the-loop architecture from consent-only to full 8-layer HITL, add real-time per-action authorization, expose reasoning traces to operators, and document governance + multi-incident response procedures.

**Epic Ticket:** `docs/jira-tickets-json/DB-E14-gap-remediation-week7.json`  
**Tasks:** DB-131 (Day 1) through DB-135 (Day 5)

---

## Mandatory Reading

1. `AGENT.md` — workflow rules
2. `docs/tasks/lessons.md` — Week 1–6 learnings
3. `docs/learning/week6-owasp-agent-governance.md`
4. `007-01-ai-daily-briefing-assistant-v2.0.0.md`
5. `docs/gaps/WEEK7-IMPLEMENTATION-GUIDE.md`
6. `docs/jira-tickets-json/DB-E14-gap-remediation-week7.json`

---

## Daily Workflow

| Day | Task | Focus |
|---|---|---|
| 1 | DB-131 | HITL layer registry |
| 2 | DB-132 | Per-action authorization |
| 3 | DB-133 | Reasoning trace observability |
| 4 | DB-134 | Governance + emergency auth |
| 5 | DB-135 | Tabletop exercises + proof |

**Per-day gate:** `uv run ruff check backend && uv run ruff format backend && uv run mypy backend && uv run pytest`

---

## Success Criteria

- 8 HITL layers in `backend/security/hitl.py`
- `per_action_authz_total` metric exported
- `ReasoningTrace` component in frontend
- `docs/GOVERNANCE.md` + `TABLETOP-EXERCISES.md` complete
- AGENT08 implemented
- 390+ tests passing
- `proof/week7/` complete

---

## Week 8 Preview

- Production optimization — DB-E15
- Agentic RAG & context engineering (Phase 6)

---

*Week 7 Kickoff — Created 2026-06-06*
