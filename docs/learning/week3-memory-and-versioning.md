# Week 3 Learning — Procedural/Episodic Memory + Prompt Versioning

**Epic:** DB-E10 Gap Remediation Week 3  
**Date:** June 2026  
**Reference:** `007-01-ai-daily-briefing-assistant-v2.0.0.md` § Memory Architecture, § Prompt Versioning

---

## Overview

Week 3 completed the CoALA four-layer memory model and added centralized prompt version management:

1. **Procedural memory** — JSON skill definitions with `allowed_agents` access control
2. **Episodic memory** — distilled session lessons (not raw logs) with version supersede
3. **Prompt version registry** — reads `CONTRACT.md` per agent, cache invalidation on change
4. **Cross-layer retrieval** — `retrieve_agent_memory()` combines all layers for Focus agent

---

## Procedural Memory (Layer 3)

| Field | Purpose |
|---|---|
| `skill_key` | Unique per user + agent |
| `definition` | JSON: steps, tools, success_criteria |
| `allowed_agents` | Progressive disclosure — only listed agents can use the skill |
| `success_count` | Rank skills by proven outcomes |

**Store:** `backend/memory/procedural.py`  
**Migration:** `003_procedural_memory`

---

## Episodic Memory (Layer 4)

| Field | Purpose |
|---|---|
| `session_id` | Isolates lessons to a briefing session |
| `lesson_type` | session_summary, disagreement, optimization, etc. |
| `version` + `superseded_by` | Rollback support without deleting history |

**Distillation:** `distill_working_to_episodic()` joins working memory snippets into a concise lesson at session end.

**Store:** `backend/memory/episodic.py`  
**Migration:** `004_episodic_memory`

---

## Prompt Version Registry

```python
from backend.prompt_version import resolve_prompt_version

version = resolve_prompt_version("focus")  # reads prompts/focus/CONTRACT.md
```

- **Format:** `v{major}.{minor}.{patch}` — matches `ExecutionMetadata.prompt_version`
- **Startup:** `register_version_snapshot()` + `check_and_invalidate_cache()`
- **Change detection:** logs `prompt_cache_version_changed` when CONTRACT.md version bumps

Focus, verification, and adversarial agents now resolve versions from CONTRACT.md instead of hardcoded constants.

---

## Cross-Layer Retrieval

```python
context = await retrieve_agent_memory(
    user_id=user_id,
    agent_id="focus",
    trace_id=trace_id,
    query_text=retrieval_query,
    working_context=snippets,
)
payload = context.to_payload()
# → semantic_memory, procedural_skills, episodic_lessons
```

Audit trail extended: `memory_layer` now includes `procedural` and `episodic`.

---

## Semantic Consolidation

`consolidate_semantic_memory()` now prunes rows older than `max_age_days` (default 90). Replaces Week 2 stub.

---

## Test Coverage

| File | Scenarios |
|---|---|
| `test_procedural.py` | 2 |
| `test_episodic.py` | 3 |
| `test_retrieval_layers.py` | 2 |
| `test_prompt_version.py` | 5 |

**Total after Week 3:** 217 tests passing (+12 from Week 2 baseline of 205).

---

## Week 4 Follow-Up

1. Live embedding API (replace deterministic vectors)
2. Orchestrator post-session episodic distillation hook
3. Critic prompt upgrade to v2.0.0 (OpenAI cache eligibility)
4. AgentOps metrics (DB-E11)

---

*Week 3 Memory & Versioning — June 2026*
