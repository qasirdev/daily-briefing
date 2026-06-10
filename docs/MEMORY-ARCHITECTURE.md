# Memory Architecture — CoALA Four-Layer Model

**Reference:** `007-01-ai-daily-briefing-assistant-v2.0.0.md` § Memory Architecture  
**Epic:** DB-E8–DB-E11 gap remediation

---

## Overview

The AI Daily Briefing Assistant implements the CoALA four-layer memory model:

| Layer | Store | Persistence | Purpose |
|---|---|---|---|
| 1 — Working | LangGraph state | Session | Ephemeral context snippets + token budget |
| 2 — Semantic | `semantic_memory` (pgvector) | Durable | Similar past briefings and preferences |
| 3 — Procedural | `procedural_memory` | Durable | JSON skill definitions with access control |
| 4 — Episodic | `episodic_memory` | Durable | Distilled session lessons (not raw logs) |

---

## Retrieval Flow

```
Working context → semantic search (pgvector)
               → procedural skills (access-filtered)
               → episodic lessons (recent, same user)
    → audit + metrics → Focus LLM payload
```

Implementation: `backend/memory/retrieval.py` → `retrieve_agent_memory()`

### Agentic RAG (Week 8, Gaps #33, #37)

Dynamic retrieval via `backend/memory/agentic_rag.py`:

- `decide_retrieval()` — skip | partial | full based on user history and MCP richness
- `refine_query()` — iterative broadening when semantic search under-delivers
- Source validation: `backend/memory/source_validation.py`
- Context compression: `backend/memory/context_compression.py`

See `docs/CONTEXT-ENGINEERING.md`.

## Security Controls (Week 4)

### RAG Poisoning Defense (Gap #120)

- Pre-ingestion validation: `backend/memory/ingestion.py`
- Content provenance: `source_trust`, `content_hash` on semantic rows
- Retrieval re-validation before LLM injection

### Memory Quarantine (Gap #132)

- Workflow: `backend/memory/quarantine.py`
- Actions: `quarantine_memory()` → review → `restore_memory()` or `delete_memory()`
- Quarantined rows excluded from semantic and episodic retrieval
- Metric: `memory_quarantine_total{memory_layer, action}`

### Privilege Retention Prevention (Gap #119)

Episodic memory must never restore active privileges across sessions.

**Rules:**

1. `sanitize_lesson_content()` redacts credentials and privilege patterns before store
2. Metadata marks `privilege_scope: session_only` — privileges are historical, not current
3. Working memory clears at session boundary; episodic lessons never imply ongoing access
4. Session distillation runs post-briefing in `orchestrator_present_node`

**Redacted patterns:** passwords, API keys, bearer tokens, admin/root access claims

Implementation: `backend/memory/privilege.py`, wired in `EpisodicMemoryStore.store_lesson()`

---

## Consolidation

| Job | Function | Metric |
|---|---|---|
| Working → Episodic | `distill_working_to_episodic()` | `memory_consolidation_duration_seconds{operation="episodic_distill"}` |
| Semantic prune | `consolidate_semantic_memory()` | `memory_consolidation_duration_seconds{operation="semantic_prune"}` |

---

## AgentOps Metrics

| Metric | Purpose |
|---|---|
| `memory_reads_total` | Reads by layer and agent |
| `memory_quarantine_total` | Quarantine workflow actions |
| `consensus_disagreement_total` | Multi-agent disagreements by level |
| `memory_consolidation_duration_seconds` | Consolidation job latency |
| `embedding_requests_total` | Live embedding API usage |

---

## Migrations

| Revision | Description |
|---|---|
| 002 | Semantic memory + pgvector |
| 003 | Procedural memory |
| 004 | Episodic memory |
| 005 | Semantic provenance + quarantine flag |
| 006 | Quarantine metadata + episodic quarantine |

Apply: `uv run alembic upgrade head`

---

*Memory Architecture — Updated Week 4 (DB-E11)*
