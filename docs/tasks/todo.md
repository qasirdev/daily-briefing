# Active Tasks — AI Daily Briefing Assistant

## Input security + compliance (2026-06-10) — complete

**Scope:** Pre-focus injection gate, API failure fields, UI security alerts, spotlighting (Gap #114), `.cursor` test coverage.

- [x] `input_security_gate` graph kernel + `input_security_result` envelope
- [x] `failure_reason` / `failure_message` on `BriefingResponse`
- [x] Red security alert in `BriefingDashboard` (no retry on injection)
- [x] `backend/security/spotlighting.py` wired into Focus LLM user context
- [x] `input-security.md` on all agent prompt packs; loader includes block in cached assembly
- [x] Docs: `docs/SECURITY.md`, `backend/graph/AGENT.md`, `frontend/AGENT.md`
- [x] Backend tests: gate, E2E API, reasoning trace, spotlighting
- [x] Frontend tests: BriefingDashboard, briefing-schema, ObservabilityBadge, ConsentPromptModal

### Verification

```bash
uv run ruff check backend && uv run ruff format backend && uv run mypy backend && uv run pytest
cd frontend && npm run test:coverage
```

### Compliance audit (2026-06-10, 3-pass)

- [x] CI runs frontend Vitest with coverage gate (`.cursor/rules/testing.mdc`)
- [x] `@vitest/coverage-v8` + 75% thresholds in `vitest.config.ts`
- [x] Tests for cost-tracking, account-usage, ReasoningTrace, expanded API/consent coverage
- [x] `frontend/AGENT.md` architecture + test matrix aligned with code

---

## Week 8 Implementation — Production Optimization & Agentic RAG

**Epic:** DB-E15  
**Branch:** `epic/week8-gap-remediation`  
**Status:** complete  
**Started:** 2026-06-06  
**Scope:** Phase 6 — Agentic RAG, context engineering, reasoning feedback, deployment gates

**Ticket file:** `docs/jira-tickets-json/DB-E15-gap-remediation-week8.json`  
**Kickoff:** `docs/gaps/WEEK8-KICKOFF-PROMPT.md`  
**Guide:** `docs/gaps/WEEK8-IMPLEMENTATION-GUIDE.md`

### Day 1: Agentic RAG Decision Engine (DB-136, Gaps #33, #37)
- [x] Create `backend/memory/agentic_rag.py`
- [x] Create `docs/CONTEXT-ENGINEERING.md`
- [x] Wire decision engine into `retrieve_agent_memory()`
- [x] Add `agentic_rag_decisions_total` metric
- [x] Write tests: `backend/tests/memory/test_agentic_rag.py`

### Day 2: Source Validation & Context Compression (DB-137, Gaps #34, #38, #40)
- [x] Create `backend/memory/source_validation.py`
- [x] Create `backend/memory/context_compression.py`
- [x] Wire into retrieval pipeline
- [x] Write tests: `backend/tests/memory/test_source_validation.py`, `test_context_compression.py`

### Day 3: Reasoning-Level Feedback (DB-138, Gap #69)
- [x] Create `backend/schemas/reasoning_feedback.py`
- [x] Create `backend/api/v1/feedback.py`
- [x] Create `frontend/components/ReasoningFeedback.tsx`
- [x] Update HITL feedback layer to implemented
- [x] Write tests: `backend/tests/test_reasoning_feedback.py`

### Day 4: Enumeration Detection & Deployment Gates (DB-139, Gaps #59, T1087)
- [x] Create `backend/security/enumeration_detector.py`
- [x] Create `backend/observability/deployment_gates.py`
- [x] Create `docs/DEPLOYMENT-GATES.md`
- [x] Update MITRE T1087 to detected
- [x] Write tests: `test_enumeration_detector.py`, `test_deployment_gates.py`

### Day 5: Integration Tests & Proof (DB-140)
- [x] Integration tests and proof artifacts

## Verification Gates (historical)

```bash
uv run ruff check backend && uv run ruff format backend && uv run mypy backend && uv run pytest
```
