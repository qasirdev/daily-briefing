# Context Engineering — IBM Four Pillars

**Gaps #33, #37, #38** | **Week 8 (DB-E136)** | **Last updated:** 2026-06-06

Context engineering is the discipline of delivering the **right data, at the right time, with the right permissions** to AI models at runtime — beyond prompt engineering alone.

---

## Four Pillars

| Pillar | Implementation | Module |
|---|---|---|
| **Connected access** | Consent-gated MCP + per-action authz before credential issue | `backend/security/per_action_authz.py` |
| **Knowledge layer** | CoALA four-layer memory (Working, Semantic, Procedural, Episodic) | `backend/memory/` |
| **Precision retrieval** | Agentic RAG decides whether/when/which layers to query | `backend/memory/agentic_rag.py` |
| **Runtime governance** | HITL layers, reasoning traces, deployment gates | `backend/security/hitl.py`, `deployment_gates.py` |

---

## Agentic RAG Flow

```
MCP data + working memory
    → decide_retrieval() — skip | partial | full | refine
    → layer-specific fetch (semantic / procedural / episodic)
    → source validation + cross-reference
    → context compression to token budget
    → Focus Agent LLM payload
```

**Decision kinds:**

| Kind | When | Layers |
|---|---|---|
| `skip` | Anonymous user | None |
| `partial` | First session or empty context | Procedural ± episodic/semantic |
| `full` | Rich MCP + working context | All three durable layers |
| `refine` | Semantic miss after first pass | Re-query with broadened terms |

Metric: `agentic_rag_decisions_total{decision, layer}`

---

## Source Validation (Gap #34)

- Exclude `source_trust=untrusted` at retrieval
- Deduplicate by content; drop conflicting `source_id` pairs
- Re-validate with `validate_semantic_content()` at ingestion and retrieval

---

## Context Compression (Gap #40)

- Truncate long `content` / `summary` fields to 400 chars
- Drop lowest-priority items (episodic → semantic → procedural) when over budget
- Default budget: `context_compression_max_chars=6000`
- Metric: `context_compression_bytes_saved_total`

---

## References

- `docs/MEMORY-ARCHITECTURE.md`
- `docs/example-code/examples/2026-12-01-youtube-IBM.md` § Context Engineering
- `007-01-ai-daily-briefing-assistant-v2.0.0.md`

---

*Context Engineering — Week 8 Gap Remediation*
