# Week 3 Implementation Guide — Procedural/Episodic Memory + Prompt Versioning

**Target:** Complete CoALA four-layer memory + centralized prompt version registry  
**Duration:** 5 days (40 hours)  
**Epic Ticket:** `docs/jira-tickets-json/DB-E10-gap-remediation-week3.json`  
**Prerequisites:** Week 2 (DB-E9) merged — Working + Semantic memory operational

---

## Implementation Protocol

### Mandatory Reading Order

1. `AGENT.md` — Root workflow rules
2. `docs/EXECUTION-RULES.md`
3. `docs/tasks/lessons.md` — Week 1 + Week 2 learnings
4. `docs/learning/week2-caching-and-memory.md`
5. `007-01-ai-daily-briefing-assistant-v2.0.0.md` — § Memory Architecture, § Prompt Versioning
6. `docs/gaps/WEEK3-KICKOFF-PROMPT.md`

### Git Branch Workflow

```bash
git checkout epic/autonomus-implementation-gap
git pull origin epic/autonomus-implementation-gap
git checkout -b epic/week3-gap-remediation
git push -u origin epic/week3-gap-remediation
```

### Backend Verification Gate

Before marking any day or task complete:

```bash
uv run ruff check backend && uv run ruff format backend && uv run mypy backend && uv run pytest
```

---

## Day 1: Procedural Memory (DB-111)

### Goals

- CoALA layer 3: learned workflows as JSON skill definitions
- Access control via `allowed_agents` list (progressive disclosure)
- RLS on `procedural_memory` table

### Schema

```sql
CREATE TABLE procedural_memory (
    id UUID PRIMARY KEY,
    user_id VARCHAR(64) NOT NULL,
    agent_id VARCHAR(50) NOT NULL,
    skill_key VARCHAR(64) NOT NULL,
    name VARCHAR(200) NOT NULL,
    definition JSONB NOT NULL,
    allowed_agents JSONB NOT NULL DEFAULT '[]',
    success_count INTEGER NOT NULL DEFAULT 0,
    last_used_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (user_id, agent_id, skill_key)
);
```

### Key Files

| File | Change |
|---|---|
| `backend/memory/procedural.py` | `ProceduralMemoryStore` — register, list, record_success |
| `backend/db/models.py` | `ProceduralMemoryRow` |
| `backend/alembic/versions/003_procedural_memory.py` | Migration + RLS |
| `backend/settings.py` | `enable_procedural_memory`, `procedural_memory_top_k` |

---

## Day 2: Episodic Memory (DB-112)

### Goals

- CoALA layer 4: distilled lessons (NOT raw logs)
- Session isolation via `user_id` + `session_id`
- Version supersede for rollback

### Schema

```sql
CREATE TABLE episodic_memory (
    id UUID PRIMARY KEY,
    user_id VARCHAR(64) NOT NULL,
    session_id VARCHAR(64) NOT NULL,
    lesson_type VARCHAR(32) NOT NULL,
    summary TEXT NOT NULL,
    version INTEGER NOT NULL DEFAULT 1,
    superseded_by UUID REFERENCES episodic_memory(id),
    metadata JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

### Key Files

| File | Change |
|---|---|
| `backend/memory/episodic.py` | `EpisodicMemoryStore` |
| `backend/memory/consolidation.py` | `distill_working_to_episodic()`, real semantic prune |
| `backend/alembic/versions/004_episodic_memory.py` | Migration + RLS |

---

## Day 3: Prompt Version Registry (DB-113)

### Goals

- Parse `## Version` from `prompts/{agent}/CONTRACT.md`
- `resolve_prompt_version(agent_id)` used by all LLM agents
- Detect version changes at startup; log cache invalidation

### Version Format

`v{major}.{minor}.{patch}` — matches `ExecutionMetadata.prompt_version` pattern

### Key Files

| File | Change |
|---|---|
| `backend/prompt_version.py` | Registry, change detection, invalidation |
| `backend/agents/*/node.py` | Replace hardcoded versions |
| `backend/main.py` | Call `check_prompt_version_changes()` on startup |

---

## Day 4: Cross-Layer Integration (DB-114)

### Goals

- `retrieve_agent_memory()` — semantic + procedural + episodic in one call
- Focus agent injects all layers into LLM payload
- Audit trail for procedural/episodic reads

### Retrieval Flow

```
Working context → semantic search (pgvector)
               → procedural skills (access-filtered)
               → episodic lessons (recent, same user)
    → audit + metrics → Focus LLM payload
```

---

## Day 5: Validation & Documentation (DB-115)

### Success Criteria

| Metric | Target |
|---|---|
| Procedural skill match | Access control enforced |
| Episodic session isolation | No cross-user bleed |
| Prompt version resolution | All agents from CONTRACT.md |
| Cross-layer integration tests | 10+ scenarios pass |

### Deliverables

- `proof/week3/` — test output, git history
- `docs/learning/week3-memory-and-versioning.md`
- Updated `docs/ARCHITECTURE.md`

---

*Week 3 Implementation Guide — Created 2026-06-06*
