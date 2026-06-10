# Graph Kernel — AGENT.md

**Scope:** LangGraph pipeline nodes that are not domain agents but enforce cross-cutting policies.

---

## Input Security Gate (`input_security_gate`)

| Property | Value |
|---|---|
| **Module** | `backend/graph/input_security_gate.py` |
| **Position** | After `parallel_task_calendar`, before `focus_agent` |
| **Role** | Agent OS kernel — pre-LLM untrusted-data scan |
| **Envelope** | `input_security_result` (`AgentResultEnvelope`, `canonical_role=supervisor`) |

### Responsibility

Scan serialised task and calendar `AgentResultEnvelope` payloads with `InputSecurityScanner` (regex + constitutional layers) **before** any Focus LLM call. Blocks prompt-injection attempts early to save tokens and prevent poisoned context reaching planners.

### Outcomes

| Scan result | Envelope `status` | Graph route |
|---|---|---|
| Clean | `success` | Continue to Focus (or consent/orchestrator branches) |
| Injection detected | `escalated` (`security_violation_detected`) | `dlq_handler` — no briefing, no retry |

### State fields set on block

- `failure_reason` — `security_violation_detected`
- `failure_message` — user-safe explanation (e.g. calendar vs task source)
- `input_security_result` — full envelope for observability and DLQ

### Relationship to Critic

The Critic Agent performs a **second** scan after Focus (task + calendar + focus JSON). Defense-in-depth: gate catches MCP-sourced injection before LLM spend; Critic catches injection introduced or echoed in focus output.

---

*See also:* `docs/SECURITY.md` · `backend/agents/critic/AGENT.md`
