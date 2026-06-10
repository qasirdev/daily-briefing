# Week 4 Learning — Memory Security, AgentOps & Live Embeddings

**Epic:** DB-E11 Gap Remediation Week 4  
**Date:** June 2026  
**Reference:** `007-01-ai-daily-briefing-assistant-v2.0.0.md` § RAG Poisoning, § Metrics Registry, § Memory Architecture

---

## Overview

Week 4 hardened the memory stack and expanded AgentOps observability:

1. **Live embeddings** — OpenRouter path in production; deterministic vectors in CI
2. **RAG poisoning defense** — ingestion validation + content hash provenance
3. **Memory quarantine** — freeze, audit, restore, or delete suspicious segments
4. **Privilege retention** — episodic summaries never store active credentials
5. **AgentOps metrics** — consensus disagreement, consolidation duration, quarantine counters
6. **Critic v2.0.0** — full 11-file prompt structure with OpenAI cache-eligible static prefix

---

## Live Embeddings (DB-116)

| Setting | CI default | Production |
|---|---|---|
| `EMBEDDING_PROVIDER` | `deterministic` | `openrouter` |
| `EMBEDDING_MODEL` | `openai/text-embedding-3-small` | same |

**Key API:** `embed_text_async()` in `backend/memory/embeddings.py`  
**Metrics:** `embedding_requests_total`, `embedding_duration_ms`

Tests use an autouse conftest fixture to force deterministic embeddings regardless of local `.env`.

---

## RAG Poisoning Defense (DB-117)

Validation runs at **store time** and again at **retrieval time** (defense in depth).

| Pattern class | Example |
|---|---|
| Instruction override | "ignore previous instructions" |
| System prompt leak | "SYSTEM PROMPT:" |
| Credentials | `api_key=`, Bearer tokens |
| HTML injection | `<script>` tags |

**Store:** `backend/memory/ingestion.py` → `validate_semantic_content()`  
**Migration:** `005_semantic_provenance.py` — `source_trust`, `content_hash`, `quarantined`

---

## Memory Quarantine (DB-118)

Workflow: **quarantine → inspect → restore or delete**

- Quarantined rows excluded from semantic vector search and episodic `get_recent_lessons`
- Audit trail via `MemoryMutationAuditEntry`
- Metric: `memory_quarantine_total{memory_layer, action}`

**Store:** `backend/memory/quarantine.py`

---

## Privilege Retention (DB-119)

Episodic lessons are sanitized before persist:

```python
from backend.memory.privilege import sanitize_lesson_content

clean = sanitize_lesson_content(raw_summary)  # redacts admin/token/password patterns
```

- Empty-after-sanitize summaries raise `ValueError` (never store credential-only blobs)
- Orchestrator calls `distill_working_to_episodic()` after presentation
- See `docs/MEMORY-ARCHITECTURE.md` for lifecycle diagram

**Metrics:** `consensus_disagreement_total`, `memory_consolidation_duration_seconds`

---

## Critic v2.0.0 (DB-120)

Upgraded from legacy 6-file layout to 11-file v2 structure (aligned with Focus and Verification):

```
prompts/critic/
├── system.md, context.md, instructions.md, examples.md
├── output-schema.md, tools.md, reasoning.md, guardrails.md
├── quality-checklist.md, CHANGELOG.md, CONTRACT.md (v2.0.0)
```

**Node wiring:**

```python
from backend.prompt_version import resolve_prompt_version

prompt_version=resolve_prompt_version("critic")  # → v2.0.0
messages = build_llm_messages("critic", user_content, ...)
```

Static prefix exceeds 1024 tokens for OpenAI automatic prompt caching (`openai_cache_eligible("critic")`).

---

## Integration Test Coverage

`backend/tests/memory/test_memory_security_integration.py` — 12 cross-layer scenarios:

- Ingestion corpus rejection
- Retrieval post-filter for poisoned hits
- Quarantine → restore lifecycle
- Privilege redaction + episodic rejection
- Critic v2 version resolution and cache eligibility

Proof artifacts: `proof/week4/`

---

## Verification Gates

```bash
uv run ruff check backend
uv run ruff format backend
uv run mypy backend
uv run pytest
uv run alembic upgrade head  # migrations 005 + 006
```

---

*Week 4 Learning — Created 2026-06-06*
