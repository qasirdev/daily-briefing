# KICKOFF PROMPT — Week 2: Prompt Caching + Memory (Option A)

**Epic:** DB-E9 — Week 2 Gap Remediation  
**Integration Branch:** `epic/autonomus-implementation-gap`  
**Feature Branch:** `epic/week2-gap-remediation`  
**Duration:** 5 days (40 hours)

**Scope:** Option A — full caching Days 1-2, Working + Semantic memory Days 3-4, validation Day 5  
**Vector Store:** pgvector on Supabase (Procedural/Episodic deferred to Week 3)

---

## Mission

Implement prompt caching (v2.0.0) for immediate token cost reduction, then establish CoALA Working + Semantic memory layers using pgvector on the existing Supabase PostgreSQL stack.

**Epic Ticket:** `docs/jira-tickets-json/DB-E9-gap-remediation-week2.json`  
**Tasks:** DB-106 (Day 1) through DB-110 (Day 5)

**Primary Deliverables:**
1. Claude `cache_control` + OpenAI auto-cache structure (Days 1-2) — DB-106, DB-107
2. Cache warming + Prometheus cache metrics — DB-106
3. Working memory in LangGraph state — DB-108
4. Semantic memory via pgvector on Supabase — DB-108, DB-109
5. Cache ROI + memory integration tests — DB-110

---

## Mandatory Reading (Before Implementation)

1. `AGENT.md`
2. `docs/EXECUTION-RULES.md`
3. `docs/tasks/lessons.md` — Week 1 learnings
4. `docs/learning/week1-consensus-pattern.md`
5. `007-01-ai-daily-briefing-assistant-v2.0.0.md` — § Prompt Caching, § Memory Architecture
6. `docs/gaps/WEEK2-IMPLEMENTATION-GUIDE.md`
7. `backend/AGENT.md`

---

## Pre-Implementation Checklist

```bash
git checkout epic/autonomus-implementation-gap
git pull origin epic/autonomus-implementation-gap
git checkout -b epic/week2-gap-remediation
git push -u origin epic/week2-gap-remediation

uv sync
uv run pytest -v   # Week 1 baseline must pass

# Verify cache metrics from Week 1
curl http://localhost:8010/metrics | grep llm_cache
```

Write plan to `docs/tasks/todo.md` before touching code.

---

## Daily Workflow

| Day | Task | Focus |
|---|---|---|
| 1 | DB-106 | Claude cache_control, cache warming, metrics |
| 2 | DB-107 | Verification/adversarial LLM, OpenAI cache validation |
| 3 | DB-108 | Working memory + pgvector semantic_memory table |
| 4 | DB-109 | Memory integration into Focus agent |
| 5 | DB-110 | Cache ROI, tests, proof package, learning doc |

**Per-day gate:** `uv run ruff check backend` → `uv run mypy backend` → `uv run pytest`

---

## Success Criteria

**Prompt Caching (Days 1-2):**
- Cache hit rate ≥70% on warm-path tests
- Token cost reduction measurable via Prometheus
- All 4 agents (focus, critic, verification, adversarial) use `build_llm_messages()`

**Memory (Days 3-4):**
- pgvector enabled on Supabase
- Semantic search <100ms
- RLS enforces user_id isolation
- Working memory token budget tracked

**Day 5:**
- `proof/week2/` complete
- `docs/learning/week2-caching-and-memory.md` written

---

## Week 3 Preview

- Procedural + Episodic memory layers
- Prompt version management (Gaps #13-18)
- DB-E10 epic ticket

---

*Week 2 Kickoff — Created 2026-06-06*
