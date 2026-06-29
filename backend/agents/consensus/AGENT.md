# Consensus Evaluator — AI Daily Briefing Assistant

**Role:** Consensus Evaluator  
**Canonical Role:** `consensus_evaluator`  
**Purpose:** Aggregate Verification, Adversarial, and Critic outputs to decide agreement level before Orchestrator synthesis

---

## Role & Purpose

The Consensus Evaluator is a deterministic graph node (not an LLM agent). It counts major, moderate, and minor concerns from upstream verifier agents and emits a structured `consensus_result` for routing.

## Input

`BriefingGraphState` with:

- `verification_result` — Verification Agent envelope
- `adversarial_result` — Adversarial Agent envelope
- `critic_result` — Critic Agent envelope

## Output

State update with `consensus_result`:

- `major_concerns`, `moderate_concerns`, `minor_concerns`
- `agreement_level` — `agreement`, `minor_disagreement`, `major_disagreement`
- `status` — routing hint for the graph builder

## Security Constraints

- Never synthesize user-facing markdown
- Never retry Critic safety violations — those route to DLQ upstream
- Major disagreement may escalate to `human_escalation` when configured

## Integration Points

- Invoked after Critic when `enable_consensus_workflow=True`
- Routes to `orchestrator_present`, `human_escalation`, or `dlq_handler` via `route_after_consensus`
- Records `consensus_disagreement_total` Prometheus metric

## Dependencies

| Dependency | Purpose |
|---|---|
| `backend/graph/builder.py` | Conditional routing after consensus |
| `backend/metrics.py` | `record_consensus_disagreement` |
