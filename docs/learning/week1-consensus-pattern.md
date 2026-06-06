# Week 1 Learning — Multi-Agent Consensus Pattern

**Epic:** DB-E8 Gap Remediation Week 1  
**Date:** June 2026  
**Reference:** IBM multi-agent recommendations (`docs/example-code/examples/2026-12-01-youtube-IBM.md`)

---

## Pattern Overview

The consensus pattern adds independent verification and adversarial review before the Critic gate. It reduces hallucination risk by requiring MCP-grounded claims and explicit disagreement handling.

```
Focus (generate) → Verification (fact-check) → Adversarial (challenge) → Consensus (route)
```

## Feature Flag Rollout

| Phase | `ENABLE_CONSENSUS_WORKFLOW` | Behavior |
|---|---|---|
| Week 1 testing | `false` (default) | Legacy Focus → Critic path |
| Week 2+ production | `true` | Full consensus pipeline |

The flag is read at graph compile time in `backend/graph/builder.py`. Consensus nodes are only registered when enabled.

## Key Implementation Decisions

### 1. Verification vs Critic

- **Verification** checks factual alignment with MCP source data
- **Critic** checks safety, injection, and plan quality
- Both return `AgentResultEnvelope`; only Orchestrator emits markdown

### 2. Concern Counting

`consensus_evaluator_node` aggregates severities:

| Source | Severity | Bucket |
|---|---|---|
| Verification (escalated) | `critical` | major |
| Verification (escalated) | `major` | moderate |
| Verification (escalated) | `minor` | minor |
| Adversarial | `severe` | major |
| Adversarial | `moderate` | moderate |
| Adversarial | `minor` | minor |

### 3. Human Escalation

When `major_concerns >= 2`, the graph routes to `human_escalation` and terminates with `status=awaiting_human_review`. Orchestrator does not run — preventing degraded briefings from reaching users.

## NHI Registry Integration

All production agents are registered in `backend/security/nhi_registry.json`. Verification and Adversarial agents should be registered before enabling the consensus flag in production (Week 2).

## Observability

- Drift detection: `guardrail_violations_total` (Day 1)
- Consensus routing: log `human_escalation_required` with `major_concerns` and `trace_id`
- Week 2: episodic memory for logged disagreements

## Test Coverage

| Test File | Scenarios |
|---|---|
| `backend/tests/observability/test_drift_detection.py` | 7 — metrics and envelope violations |
| `backend/tests/security/test_nhi.py` | 7 — NHI registry |
| `backend/tests/architecture/test_consensus.py` | 3 — agreement, escalation, minor disagreement |

## Week 2 Follow-Up

1. Full LLM-backed Verification and Adversarial nodes (replace stubs)
2. Register `nhi_verification_agent_v1` and `nhi_adversarial_agent_v1`
3. Enable `ENABLE_CONSENSUS_WORKFLOW=true` in staging
4. Episodic memory for disagreement logging

---

*Week 1 Consensus Pattern — June 2026*
