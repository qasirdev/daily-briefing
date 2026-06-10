# HITL Architecture — AI Daily Briefing Assistant

**Gaps #66, #95** | **Week 7 (DB-E14)** | **IBM Multi-Agent Pattern**

Human-in-the-loop (HITL) is architectural — not a safety net bolted on after automation. Standard briefing runs use **human-on-the-loop** (autonomous with visible override). Sensitive or scope-expanding actions require **human-in-the-loop** gates.

---

## Operating Modes

| Mode | When | User Experience |
|---|---|---|
| **Human-on-the-loop** | Default briefing generation | Agents run autonomously; user sees reasoning trace and can revoke consent or deny escalation |
| **Human-in-the-loop** | Consensus disagreement, high-impact actions | Pipeline pauses at `awaiting_human_review`; user must approve before resume |

Declared in `docs/AGENTIC-CONSENT.md` § Human-on-the-Loop Default.

---

## Eight HITL Layers

| Layer | Owner | Implementation | Test |
|---|---|---|---|
| **Input** | Human | `BriefingRequest` + consent TTL selection | `test_consent.py` |
| **Planning** | Agent | Focus Agent work plan | `test_focus_memory.py` |
| **Review** | Shared | Verification + Adversarial + Critic | `test_consensus.py` |
| **Revision** | Agent | Critic revision loop (`revision_count` cap) | `test_graph.py` |
| **Execution** | Agent | MCP calls with per-action authz | `test_per_action_authz.py` |
| **Monitoring** | Shared | Reasoning traces + drift metrics | `test_reasoning_trace.py` |
| **Override** | Human | Consent deny/revoke, human escalation | `test_hitl_layers.py` |
| **Feedback** | Human | Episodic memory distillation (partial UI) | `test_episodic.py` |

Registry: `backend/security/hitl.py` — `HITL_LAYERS`, `layer_summary()`.

---

## Reasoning Observability

Every briefing response includes `reasoning_trace` with per-agent steps mapped to HITL layers.

- Backend: `backend/observability/reasoning_trace.py`
- Frontend: `frontend/components/ReasoningTrace.tsx`
- API field: `BriefingResponse.reasoning_trace`

---

## Override & Rollback

See `docs/OVERRIDE-ROLLBACK.md` for pause, override, and rollback procedures.

---

*HITL Architecture — Week 7 Gap Remediation*
