# Week 2 Implementation Guide — Prompt Caching + Memory (Option A)

**Target:** Prompt caching ROI (Days 1-2) + Working/Semantic memory via pgvector (Days 3-4)  
**Duration:** 5 days (40 hours)  
**Epic Ticket:** `docs/jira-tickets-json/DB-E9-gap-remediation-week2.json`  
**Scope Decision:** Option A — defer Procedural/Episodic memory to Week 3  
**Vector Store:** pgvector on Supabase (existing PostgreSQL + RLS)

---

## Implementation Protocol

### Mandatory Reading Order

1. `AGENT.md` — Root workflow rules
2. `docs/EXECUTION-RULES.md` — Production-ready code requirements
3. `docs/tasks/lessons.md` — Week 1 learnings (consensus flag, trace IDs, NHI patterns)
4. `docs/learning/week1-consensus-pattern.md`
5. `007-01-ai-daily-briefing-assistant-v2.0.0.md` — § Prompt Caching, § Memory Architecture
6. `docs/gaps/WEEK2-KICKOFF-PROMPT.md`
7. `backend/AGENT.md`

### Git Branch Workflow

```bash
git checkout epic/autonomus-implementation-gap
git pull origin epic/autonomus-implementation-gap
git checkout -b epic/week2-gap-remediation
git push -u origin epic/week2-gap-remediation
```

---

## Day 1: Claude Prompt Caching (DB-106)

### Goals

- Static prompt blocks with `cache_control: ephemeral` for Claude models
- Stable system prefix ≥1024 tokens for OpenAI auto-cache
- Cache warming on startup + periodic refresh (4 min interval, before 5 min TTL)
- Prometheus cache metrics wired from LLM usage

### Implementation

| File | Change |
|---|---|
| `backend/prompts_loader.py` | `build_cached_prompt_assembly()` — v2.0.0 + legacy file order |
| `backend/llm/prompt_cache.py` | `build_llm_messages()`, `PromptCacheWarmer` |
| `backend/llm/router.py` | Cache usage extraction, metrics recording |
| `backend/observability/metrics.py` | `record_llm_cache_usage()`, `set_cache_size_bytes()` |
| `backend/settings.py` | `enable_prompt_caching`, `prompt_cache_warm_*` |
| `backend/main.py` | Startup warm + background loop |
| `backend/agents/focus/node.py` | Use `build_llm_messages()` |
| `backend/agents/critic/node.py` | Use `build_llm_messages()` |

### Prompt Block Order (static → dynamic)

```
system → context → instructions → examples → tools → reasoning → guardrails
[user message — NEVER cached]
```

### Verification

```bash
uv run ruff check backend
uv run mypy backend
uv run pytest backend/tests/llm/test_prompt_cache.py -v
curl http://localhost:8010/metrics | grep llm_cache
```

---

## Day 2: OpenAI Caching + Verification/Adversarial LLM (DB-107)

### Goals

- Replace heuristic stubs with LLM-backed verification/adversarial nodes
- Validate cache hit rates for all 4 cached agents
- Prompt version bumps in CONTRACT.md / CHANGELOG.md

### Key Files

- `backend/agents/verification/node.py`
- `backend/agents/adversarial/node.py`
- `prompts/verification/*`, `prompts/adversarial/*`

---

## Day 3: Working Memory + Semantic Memory Foundation (DB-108)

### Goals

- Working memory: LangGraph state extensions + token budget tracking
- Semantic memory: pgvector on Supabase

### pgvector Setup (Supabase)

```sql
-- Run via Alembic migration
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE semantic_memory (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(64) NOT NULL,
    content TEXT NOT NULL,
    embedding vector(1536) NOT NULL,
    source_type VARCHAR(32) NOT NULL,
    source_id VARCHAR(64),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX semantic_memory_embedding_idx
    ON semantic_memory USING hnsw (embedding vector_cosine_ops);

ALTER TABLE semantic_memory ENABLE ROW LEVEL SECURITY;
CREATE POLICY semantic_memory_user_isolation
    ON semantic_memory FOR ALL
    USING (user_id = current_setting('app.user_id', true));
```

### Key Files

- `backend/memory/working.py`
- `backend/memory/semantic.py`
- `backend/memory/embeddings.py`
- `backend/alembic/versions/002_semantic_memory_pgvector.py`

### Apply migration (repo root)

Alembic config lives at **`alembic.ini`** (project root), not `backend/alembic.ini`.
`script_location = backend/alembic` points at the migration scripts directory.

```bash
# from daily-briefing/ (repo root)
uv run alembic upgrade head
```

---

## Day 4: Memory Integration (DB-109)

### Goals

- Focus agent retrieves top-k similar briefings before LLM call
- Working memory token budget exposed via metrics
- Memory reads in audit trail

---

## Day 5: Validation & Documentation (DB-110)

### Success Criteria

| Metric | Target |
|---|---|
| Cache hit rate (warm path) | ≥70% |
| Semantic search latency | <100ms |
| Working memory access | <10ms |
| Unit test coverage (memory) | ≥80% |

### Deliverables

- `proof/week2/` — test output, cache metrics snapshot
- `docs/learning/week2-caching-and-memory.md`
- Updated `docs/ARCHITECTURE.md`

---

*Week 2 Implementation Guide — Created 2026-06-06*
