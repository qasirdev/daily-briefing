# KICKOFF PROMPT — Week 4: Memory Security, AgentOps & Live Embeddings

**Epic:** DB-E11 — Week 4 Gap Remediation  
**Integration Branch:** `epic/autonomus-implementation-gap`  
**Feature Branch:** `epic/week4-gap-remediation`  
**Duration:** 5 days (40 hours)

**Scope:** Phase 2 — memory hardening, live embeddings, AgentOps metrics, Critic v2.0.0

---

## Mission

Harden the four-layer memory system against poisoning and privilege retention, replace deterministic semantic vectors with live embeddings when configured, expand AgentOps observability, and upgrade the Critic agent to v2.0.0 prompt standards.

**Epic Ticket:** `docs/jira-tickets-json/DB-E11-gap-remediation-week4.json`  
**Tasks:** DB-116 (Day 1) through DB-120 (Day 5)

**Primary Deliverables:**
1. Live embedding API via OpenRouter (DB-116)
2. RAG poisoning defense — pre-ingestion validation (DB-117, Gap #120)
3. Memory quarantine workflow (DB-118, Gap #132)
4. Privilege retention prevention + AgentOps metrics (DB-119, Gaps #119, #58-61)
5. Critic v2.0.0 + proof package (DB-120)

---

## Mandatory Reading (Before Implementation)

1. `AGENT.md`
2. `docs/EXECUTION-RULES.md`
3. `docs/tasks/lessons.md` — Week 1–3 learnings
4. `docs/learning/week3-memory-and-versioning.md`
5. `007-01-ai-daily-briefing-assistant-v2.0.0.md` — § RAG Poisoning Defense, § Metrics Registry
6. `docs/gaps/WEEK4-IMPLEMENTATION-GUIDE.md`
7. `backend/AGENT.md`

---

## Pre-Implementation Checklist

```bash
git checkout epic/autonomus-implementation-gap
git pull origin epic/autonomus-implementation-gap
git checkout -b epic/week4-gap-remediation   # or checkout existing branch
git push -u origin epic/week4-gap-remediation

uv sync
uv run pytest -v   # Week 3 baseline must pass (217+)

# Verify memory + prompt version metrics
curl http://localhost:8010/metrics | grep -E 'memory_reads|prompt_cache|semantic_search'
```

Write plan to `docs/tasks/todo.md` before touching code.

---

## Daily Workflow

| Day | Task | Focus |
|---|---|---|
| 1 | DB-116 | Live embedding API (OpenRouter + deterministic fallback) |
| 2 | DB-117 | RAG poisoning defense — ingestion validation |
| 3 | DB-118 | Memory quarantine workflow |
| 4 | DB-119 | Privilege retention + AgentOps metrics |
| 5 | DB-120 | Critic v2.0.0, tests, proof package |

**Per-day gate:** `uv run ruff check backend` → `uv run ruff format backend` → `uv run mypy backend` → `uv run pytest`

---

## Success Criteria

**Live Embeddings (Day 1):**
- `EMBEDDING_PROVIDER=openrouter` uses `text-embedding-3-small` via OpenRouter
- CI/tests remain on deterministic provider (no API key required)
- Focus and retrieval paths use async embedding

**Memory Security (Days 2-3):**
- Poisoned content blocked at ingestion
- Quarantined memory excluded from retrieval
- Security metrics increment on block/quarantine

**AgentOps (Day 4):**
- Consensus disagreement tracked
- Episodic distillation runs post-session
- Privileges never persist across sessions

**Day 5:**
- Critic prompt ≥1024 tokens static prefix (OpenAI cache eligible)
- `proof/week4/` complete
- `docs/learning/week4-memory-security-and-agentops.md` written

---

## Week 5 Preview

Week 5 materials are ready — start with `docs/gaps/WEEK5-KICKOFF-PROMPT.md`:

- **Epic:** DB-E12 — Supply chain security + JIT credentials
- **Tasks:** DB-121 (AI-BOM) → DB-125 (vendor assessments + proof)
- **Ticket format:** `docs/jira-tickets-json/DB-E12-gap-remediation-week5.json` (DB-E2 `Description` pattern)

---

*Week 4 Kickoff — Created 2026-06-06*
