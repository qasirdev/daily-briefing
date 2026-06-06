# Week 2 Implementation — Prompt Caching + Memory (Option A)

**Epic:** DB-E9  
**Branch:** `epic/week2-gap-remediation`  
**Status:** in_progress  
**Started:** 2026-06-06  
**Scope:** Option A + pgvector (Supabase)

### Day 1: Claude Prompt Caching (DB-106)
- [x] Extend `backend/prompts_loader.py` with cacheable static block assembly
- [x] Create `backend/llm/prompt_cache.py` (build_llm_messages, PromptCacheWarmer)
- [x] Wire cache metrics in `backend/llm/router.py`
- [x] Add cache warming on startup in `backend/main.py`
- [x] Update Focus and Critic agents to use `build_llm_messages()`
- [x] Add settings: `enable_prompt_caching`, `prompt_cache_warm_*`
- [x] Write tests: `backend/tests/llm/test_prompt_cache.py`
- [x] Verify: ruff + mypy + pytest (153 passed)
- [x] Update docs/tasks/lessons.md
- [x] Commit: "Day 1: Claude prompt caching with cache warming"

### Day 2: OpenAI Caching + Verification/Adversarial LLM (DB-107)
- [x] Wire verification/adversarial nodes to LLM with cached prompts
- [x] Validate OpenAI auto-cache (≥1024 token stable prefix)
- [x] Bump prompt versions in CONTRACT.md / CHANGELOG.md (v1.1.0)
- [x] Cache hit rate validation via Prometheus (metrics tests extended)
- [x] Verify: ruff + mypy + pytest (162 passed)
- [x] Commit: "Day 2: Verification/adversarial LLM with cached prompts"

### Day 3: Working Memory + Semantic Memory Foundation (DB-108)
- [x] Create `backend/memory/working.py` (LangGraph session state)
- [x] Alembic migration: enable pgvector on Supabase (`uv run alembic upgrade head` from repo root)
- [x] Create `semantic_memory` table with HNSW index + RLS
- [x] Create `backend/memory/semantic.py` store
- [x] Create `backend/memory/embeddings.py` (deterministic embeddings for tests)
- [x] Extend `BriefingGraphState` with working memory fields
- [x] Initialize working memory in orchestrator route node
- [x] Write tests: `backend/tests/memory/`
- [x] Verify: ruff + mypy + pytest
- [x] Commit: "Day 3: Working memory and pgvector semantic memory foundation"

### Day 4: Memory Integration (DB-109)
- [x] Wire semantic retrieval into Focus agent
- [x] Working memory token budget in graph state + Prometheus metrics
- [x] Memory read audit logging
- [x] Write tests: `backend/tests/memory/test_retrieval.py`, `test_audit.py`, `test_focus_memory.py`
- [x] Verify: ruff + mypy + pytest
- [x] Commit: "Day 4: Focus memory integration with semantic retrieval and audit trail"

### Day 5: Validation & Documentation (DB-110)
- [ ] Cache ROI measurement vs Week 1 baseline
- [ ] Memory integration tests (10+ scenarios)
- [ ] Proof package in `proof/week2/`
- [ ] `docs/learning/week2-caching-and-memory.md`

---

## Verification Gates
- Each day's tests must pass before proceeding
- Backend gate: `uv run ruff check backend` → `uv run mypy backend` → `uv run pytest`
- Cache metrics visible at `/metrics` (llm_cache_hit_rate, llm_cache_hit_total, llm_cache_miss_total)

---

*Last Updated: 2026-06-06*
