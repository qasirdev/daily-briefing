# Week 7 Implementation Guide — HITL Layers & Governance Hardening

**Target:** Phase 5 gap remediation — full HITL architecture, per-action authz, governance, tabletop  
**Duration:** 5 days (40 hours)  
**Epic Ticket:** `docs/jira-tickets-json/DB-E14-gap-remediation-week7.json`  
**Prerequisites:** Week 6 (DB-E13) complete — OWASP Agent Top 10, constitutional classifiers, 364+ tests

---

## Day 1: HITL Architecture (DB-131)

| File | Purpose |
|---|---|
| `backend/security/hitl.py` | 8-layer HITL registry |
| `docs/HITL-ARCHITECTURE.md` | Layer documentation |
| `docs/AGENTIC-CONSENT.md` | Human-on-the-loop default |
| `backend/tests/security/test_hitl_layers.py` | Per-layer validation |

---

## Day 2: Per-Action Authorization (DB-132)

| File | Purpose |
|---|---|
| `backend/security/policy_engine.py` | ABAC evaluation |
| `backend/security/per_action_authz.py` | Authorizer layer |
| `backend/security/vault.py` | Wire authz before credential issue |
| `backend/tests/security/test_per_action_authz.py` | Authz scenarios |

Metric: `per_action_authz_total{service, action, outcome}`

---

## Day 3: Reasoning Trace (DB-133)

| File | Purpose |
|---|---|
| `backend/observability/reasoning_trace.py` | Trace collector |
| `backend/schemas/reasoning_trace.py` | Pydantic schemas |
| `frontend/components/ReasoningTrace.tsx` | UI component |
| `docs/OVERRIDE-ROLLBACK.md` | Override procedures |

---

## Day 4: Governance (DB-134)

| File | Purpose |
|---|---|
| `docs/GOVERNANCE.md` | Organizational governance + emergency tiers |
| `docs/INCIDENT-RESPONSE.md` | Incident workflow |
| `backend/security/owasp_agent.py` | AGENT08 → implemented |

---

## Day 5: Tabletop & Proof (DB-135)

| File | Purpose |
|---|---|
| `docs/security/TABLETOP-EXERCISES.md` | 5-incident scenario |
| `docs/security/incident-response-playbook.md` | Parallel triage |
| `proof/week7/` | Proof package |

---

## Success Criteria

| Metric | Target |
|---|---|
| HITL layers | 8/8 registered |
| Per-action authz | Before every credential issue |
| AGENT08 | Implemented |
| Tabletop scenarios | 5 simultaneous incidents |
| Tests | 390+ passing |

---

## Backend Verification Gate

```bash
uv run ruff check backend && uv run ruff format backend && uv run mypy backend && uv run pytest
```

---

*Week 7 Implementation Guide — Created 2026-06-06*
