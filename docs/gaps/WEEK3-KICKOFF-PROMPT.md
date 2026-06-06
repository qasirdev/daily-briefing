# KICKOFF PROMPT — Week 3: Procedural/Episodic Memory + Prompt Versioning

**Epic:** DB-E10 — Week 3 Gap Remediation  
**Integration Branch:** `epic/autonomus-implementation-gap`  
**Feature Branch:** `epic/week3-gap-remediation`  
**Duration:** 5 days (40 hours)

**Scope:** Complete CoALA memory (Procedural + Episodic) + prompt version registry with cache invalidation

---

## Mission

Complete the four-layer CoALA memory architecture deferred from Week 2 and establish centralized prompt version management with cache invalidation on version bumps.

**Epic Ticket:** `docs/jira-tickets-json/DB-E10-gap-remediation-week3.json`  
**Tasks:** DB-111 (Day 1) through DB-115 (Day 5)

**Primary Deliverables:**
1. Procedural memory — learned workflows with access control (DB-111)
2. Episodic memory — distilled session lessons with versioning (DB-112)
3. Prompt version registry from CONTRACT.md + cache invalidation (DB-113)
4. Cross-layer memory retrieval in Focus agent (DB-114)
5. Integration tests, proof package, learning doc (DB-115)

---

## Mandatory Reading (Before Implementation)

1. `AGENT.md`
2. `docs/EXECUTION-RULES.md`
3. `docs/tasks/lessons.md` — Week 1 + Week 2 learnings
4. `docs/learning/week2-caching-and-memory.md`
5. `007-01-ai-daily-briefing-assistant-v2.0.0.md` — § Memory Architecture, § Prompt Versioning
6. `docs/gaps/WEEK3-IMPLEMENTATION-GUIDE.md`
7. `backend/AGENT.md`

---

## Pre-Implementation Checklist

```bash
git checkout epic/autonomus-implementation-gap
git pull origin epic/autonomus-implementation-gap
git checkout -b epic/week3-gap-remediation
git push -u origin epic/week3-gap-remediation

uv sync
uv run pytest -v   # Week 2 baseline must pass (205+)

# Verify Week 2 memory + cache metrics
curl http://localhost:8010/metrics | grep -E 'llm_cache|memory_reads|working_memory'
```

Write plan to `docs/tasks/todo.md` before touching code.

---

## Daily Workflow

| Day | Task | Focus |
|---|---|---|
| 1 | DB-111 | Procedural memory store + migration |
| 2 | DB-112 | Episodic memory + working→episodic distillation |
| 3 | DB-113 | Prompt version registry + cache invalidation |
| 4 | DB-114 | Cross-layer retrieval + Focus integration |
| 5 | DB-115 | Tests, proof package, learning doc |

**Per-day gate:** `uv run ruff check backend` → `uv run ruff format backend` → `uv run mypy backend` → `uv run pytest`

---

## Success Criteria

**Procedural Memory (Day 1):**
- Skills stored with JSON definitions and allowed_agents access control
- Progressive disclosure: agents see only skills they are permitted to use

**Episodic Memory (Day 2):**
- Distilled lessons (not raw logs) with session isolation
- Version supersede support for rollback

**Prompt Versioning (Day 3):**
- All LLM agents resolve version from CONTRACT.md
- Version change triggers cache invalidation log

**Integration (Day 4):**
- Focus agent receives semantic + procedural + episodic context
- Semantic consolidation prunes stale vectors

**Day 5:**
- `proof/week3/` complete
- `docs/learning/week3-memory-and-versioning.md` written

---

## Week 4 Preview

- AgentOps metrics & evaluation (DB-E11)
- Live embedding API (replace deterministic vectors)
- Critic prompt upgrade to v2.0.0 (≥1024 tokens for OpenAI cache)

---

*Week 3 Kickoff — Created 2026-06-06*
