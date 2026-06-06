# Week 4 Implementation — Memory Security, AgentOps & Live Embeddings

**Epic:** DB-E11  
**Branch:** `epic/week4-gap-remediation`  
**Status:** in progress  
**Started:** 2026-06-06  
**Scope:** Phase 2 gap remediation — embeddings, memory security, AgentOps, Critic v2.0.0

### Day 1: Live Embedding API (DB-116)
- [x] Add `embedding_provider` + `embedding_model` settings
- [x] Implement `embed_text_async()` with OpenRouter client
- [x] Update Focus agent + retrieval to use async embeddings
- [x] Add embedding Prometheus metrics
- [x] Extend tests: `backend/tests/memory/test_embeddings.py`
- [x] Verify: ruff + mypy + pytest (221 passed)

### Day 2: RAG Poisoning Defense (DB-117)
- [x] Create `backend/memory/ingestion.py`
- [x] Alembic migration 005: provenance + quarantine columns
- [x] Wire validation into `SemanticMemoryStore.store()`
- [x] Write tests: `backend/tests/memory/test_ingestion.py`
- [x] Verify: ruff + mypy + pytest (235 passed)

### Day 3: Memory Quarantine (DB-118)
- [x] Create `backend/memory/quarantine.py`
- [x] Exclude quarantined rows from semantic/episodic retrieval
- [x] Add `memory_quarantine_total` metric
- [x] Write tests: `backend/tests/memory/test_quarantine.py`
- [x] Verify: ruff + mypy + pytest (240 passed)

### Day 4: Privilege Retention + AgentOps (DB-119)
- [ ] Episodic privilege sanitization
- [ ] Orchestrator post-session distillation hook
- [ ] `consensus_disagreement_total`, `memory_consolidation_duration` metrics
- [ ] Create/update `docs/MEMORY-ARCHITECTURE.md`
- [ ] Verify: ruff + mypy + pytest

### Day 5: Critic v2.0.0 + Proof (DB-120)
- [ ] Upgrade `prompts/critic/` to 11-file v2.0.0 structure
- [ ] Wire Critic node to `resolve_prompt_version()` + `build_llm_messages()`
- [ ] Memory security integration tests (10+ scenarios)
- [ ] Proof package in `proof/week4/`
- [ ] `docs/learning/week4-memory-security-and-agentops.md`
- [ ] Verify: ruff + mypy + pytest

---

## Verification Gates
- Backend gate: `uv run ruff check backend` → `uv run ruff format backend` → `uv run mypy backend` → `uv run pytest`
- Apply migrations: `uv run alembic upgrade head` (005 + 006)

---

*Last Updated: 2026-06-06*
