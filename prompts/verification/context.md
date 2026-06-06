# Verification Agent Context

**Version:** 1.0.0  
**Last Updated:** 2026-06-06

---

## Why This Agent Exists

LLM planners can hallucinate meeting times, invent tasks, or misstate priorities. The Verification Agent closes that gap by enforcing **source grounding** before the briefing reaches users.

## Design Principles

- **Independence:** Verify against MCP data, not Focus reasoning
- **Precision:** Every flagged claim cites `source_truth` from MCP fields
- **Proportionality:** Minor subjective wording issues are `minor`; invented events are `critical`
- **Fail-safe:** When MCP data is missing, escalate rather than guess

## Pipeline Position

Runs after Focus Agent, before Adversarial Agent and Consensus Evaluator.
