# Week 7 Learnings — HITL Layers & Governance Hardening

**Date:** 2026-06-06  
**Epic:** DB-E14

---

## Key Implementations

### 8-Layer HITL Registry

IBM HITL model codified in `backend/security/hitl.py` — maps each layer to existing controls rather than building parallel infrastructure. Feedback layer remains partial (episodic distillation without full reasoning-feedback UI).

### Per-Action Authorization

`PolicyEngine` re-reads consent on every authorization decision — no stale session cache. Wired into `CredentialBroker.get_credential()` so privilege revocation takes effect on next MCP call within credential TTL window.

### Reasoning Trace

`collect_reasoning_traces()` derives observability from existing `AgentResultEnvelope` entries in graph state — zero changes to individual agent nodes. Frontend `ReasoningTrace` component exposes HITL layer mapping to users.

### Governance & Tabletop

`GOVERNANCE.md` defines emergency Tier 1/2/3 authorization. `TABLETOP-EXERCISES.md` documents 5 simultaneous incidents with priority matrix for quarterly exercises.

---

## Patterns to Reuse

- Registry pattern (`hitl.py` mirrors `owasp_agent.py`, `mitre_coverage.py`)
- Fail-closed policy engine with fresh consent lookup
- Trace collection from graph state vs instrumenting every node

---

## Week 8 Handoff

- Feedback layer → full reasoning-level feedback UI
- T1087 enumeration detection anomaly rules
- Production optimization (DB-E15)

---

*Week 7 Learning Doc — Created 2026-06-06*
