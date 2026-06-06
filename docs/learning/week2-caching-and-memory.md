# Week 2 Learning — Prompt Caching & CoALA Memory

**Epic:** DB-E9 Gap Remediation Week 2  
**Date:** June 2026  
**Reference:** `007-01-ai-daily-briefing-assistant-v2.0.0.md` § Prompt Caching, § Memory Architecture

---

## Overview

Week 2 delivered two cost/quality improvements on top of the Week 1 consensus foundation:

1. **Prompt caching** — static agent prompts cached at the provider (Claude ephemeral blocks + OpenAI auto-cache ≥1024 tokens)
2. **CoALA memory (Option A)** — Working memory in LangGraph state + Semantic memory via pgvector on Supabase

Procedural and Episodic memory layers are deferred to Week 3.

---

## Prompt Caching Architecture

### Static vs dynamic content

```
system → context → instructions → examples → tools → reasoning → guardrails
[user message — NEVER cached]
```

Implementation: `backend/prompts_loader.py` → `backend/llm/prompt_cache.py` → `build_llm_messages()`

### Cache-eligible agents (Week 2)

| Agent | Prompt version | Cache eligible | Notes |
|---|---|---|---|
| Focus | v2.0.0 | ✅ | ≥1024 token static prefix |
| Verification | v1.1.0 | ✅ | LLM-backed with cached prompts |
| Adversarial | v1.1.0 | ✅ | LLM-backed with cached prompts |
| Critic | legacy ~140 tokens | ❌ | Below OpenAI auto-cache threshold |

### Cache warming

- Startup + background loop every 240s (before 5 min Claude TTL)
- Gated on `OPENROUTER_API_KEY` or `LOCAL_LLM_ENABLED`
- Settings: `enable_prompt_caching`, `prompt_cache_warm_interval_seconds`, `prompt_cache_warm_agents`

### Prometheus metrics

| Metric | Purpose |
|---|---|
| `llm_cache_hit_rate` | Hit rate % by provider/model |
| `llm_cache_hit_total` | Cache hits |
| `llm_cache_miss_total` | Cache misses |
| `llm_cache_size_bytes` | Static prefix size |

### Cache ROI vs Week 1

Week 1 had **0% cache hit rate** (metrics infrastructure only). Week 2 warm-path validation target: **≥70% hit rate**.

Helpers in `backend/llm/cache_roi.py`:

```python
calculate_cache_hit_rate_percent(hits=7, misses=3)  # → 70.0
cache_roi_vs_week1_baseline(hit_rate_percent=80.0)  # → +80.0 vs baseline
```

Validated in `backend/tests/llm/test_cache_roi.py`.

---

## CoALA Memory Architecture (Option A)

### Layer 1 — Working memory (ephemeral)

- **Scope:** Single LangGraph session
- **State fields:** `working_memory_tokens`, `working_memory_limit`, `working_memory_context`
- **Manager:** `backend/memory/working.py`
- **Init:** `orchestrator_route_node` at graph start
- **Updates:** After Focus (and future agents) via `record_agent_turn()`
- **Metric:** `working_memory_utilization` gauge

### Layer 2 — Semantic memory (pgvector)

- **Store:** `backend/memory/semantic.py` → `SemanticMemoryStore`
- **Table:** `semantic_memory` with HNSW index + RLS (`app.user_id`)
- **Migration:** `002_semantic_memory_pgvector` — run `uv run alembic upgrade head` from repo root
- **Embeddings:** Deterministic hash vectors for tests/dev (`backend/memory/embeddings.py`); live API deferred
- **Retrieval:** `backend/memory/retrieval.py` — cross-layer query from working context + MCP data

### Focus integration flow

```
Working memory context → build retrieval query → embed → pgvector search
    → audit log → inject semantic_memory[] into Focus LLM payload
    → generate plan → store summary back to semantic memory
    → update working memory tokens/context
```

### Audit trail

Every memory read emits:

- Structured log: `memory_read_audit`
- Counter: `memory_reads_total{memory_layer, agent_id}`
- Latency: `semantic_search_duration_ms{agent_id}`

Implementation: `backend/memory/audit.py`

### Consolidation (stub)

`backend/memory/consolidation.py` — nightly prune/merge stub for Week 3.

---

## Key Design Decisions

| Decision | Rationale |
|---|---|
| pgvector on Supabase | Reuse existing PostgreSQL + RLS; no Pinecone/Weaviate |
| Retrieval in separate module | Keeps store pure; audit + metrics at integration layer |
| DB failures are non-fatal | Focus planning continues if semantic search fails |
| Defense in depth | Explicit `user_id` filter even with RLS enabled |
| Alembic config at repo root | `alembic.ini` with `script_location = backend/alembic` |

---

## Test Coverage

| Test File | Scenarios | Focus |
|---|---|---|
| `backend/tests/llm/test_prompt_cache.py` | 12 | Cache assembly, metrics, router |
| `backend/tests/llm/test_cache_roi.py` | 8 | ROI vs Week 1, warm-path ≥70% |
| `backend/tests/memory/test_working.py` | 5 | Token budget, snippets |
| `backend/tests/memory/test_semantic.py` | 3 | Store, search |
| `backend/tests/memory/test_embeddings.py` | 4 | Deterministic vectors |
| `backend/tests/memory/test_retrieval.py` | 4 | Cross-layer query |
| `backend/tests/memory/test_audit.py` | 2 | Audit trail |
| `backend/tests/memory/test_integration.py` | 15 | End-to-end integration |
| `backend/tests/agents/test_focus_memory.py` | 2 | Focus agent wiring |

**Total Week 2 memory + cache tests:** 55+ scenarios across dedicated files.

---

## Week 3 Follow-Up

1. Live embedding API (replace deterministic vectors)
2. Procedural + Episodic memory layers
3. Verification agent semantic context
4. Nightly consolidation job (replace stub)
5. Enable `ENABLE_CONSENSUS_WORKFLOW=true` in staging with full cache + memory path

---

*Week 2 Caching & Memory — June 2026*
