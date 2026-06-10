# KICKOFF PROMPT — Week 6: OWASP Agent Top 10 & Advanced Defenses

**Epic:** DB-E13 — Week 6 Gap Remediation  
**Integration Branch:** `epic/autonomus-implementation-gap`  
**Feature Branch:** `epic/week6-gap-remediation`  
**Duration:** 5 days (40 hours)

**Scope:** Phase 4 — OWASP Agent Top 10, constitutional classifiers, MITRE ATT&CK, long-term drift, dwell time SLO, alert coverage, consent hardening

---

## Mission

Expand security posture from OWASP GenAI LLM Top 10 to full **OWASP Agent Top 10**, add multi-layer jailbreak defense via constitutional classifiers, map detections to MITRE ATT&CK, and implement measurement SLOs for dwell time and alert investigation coverage.

**Epic Ticket:** `docs/jira-tickets-json/DB-E13-gap-remediation-week6.json`  
**Tasks:** DB-126 (Day 1) through DB-130 (Day 5)

---

## Mandatory Reading

1. `AGENT.md` — workflow rules
2. `docs/tasks/lessons.md` — Week 1–5 learnings
3. `docs/learning/week5-supply-chain-and-credentials.md`
4. `007-01-ai-daily-briefing-assistant-v2.0.0.md` — § MITRE ATT&CK, Dwell Time SLO
5. `docs/gaps/WEEK6-IMPLEMENTATION-GUIDE.md`
6. `docs/jira-tickets-json/DB-E13-gap-remediation-week6.json`

---

## Daily Workflow

| Day | Task | Focus |
|---|---|---|
| 1 | DB-126 | OWASP Agent Top 10 matrix |
| 2 | DB-127 | Constitutional classifiers |
| 3 | DB-128 | MITRE ATT&CK coverage |
| 4 | DB-129 | Drift, dwell time, alert coverage |
| 5 | DB-130 | Red teaming, consent modal, proof |

**Per-day gate:** `uv run ruff check backend && uv run ruff format backend && uv run mypy backend && uv run pytest`

---

## Success Criteria

- OWASP Agent Top 10 matrix in `docs/SECURITY.md`
- Jailbreak corpus ≥95% block rate
- MITRE coverage ≥80%
- `action_payload` shown in consent modal
- 310+ tests passing
- `proof/week6/` complete

---

## Week 7 Preview

- HITL layers + governance hardening — DB-E14
- Multi-incident chaos testing (Gap #130)
- Emergency change authorization (Gap #131)

---

*Week 6 Kickoff — Created 2026-06-06*
