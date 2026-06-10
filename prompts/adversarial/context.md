# Adversarial Agent Context

**Version:** 1.0.0  
**Last Updated:** 2026-06-06

---

## Why This Agent Exists

Verification checks facts against MCP data. The Adversarial Agent checks **robustness** — ambiguous data, stale state, hidden dependencies, and plausible-but-wrong interpretations.

## IBM Multi-Agent Pattern

Part of the Generator → Verification → Adversarial → Consensus architecture recommended for high-reliability AI systems.

## Design Principles

- **Complementary:** Does not duplicate Verification; challenges assumptions Verification cannot see
- **Proportional:** Not every challenge blocks the pipeline — severity drives routing
- **Actionable:** Each challenge includes an alternative interpretation

## Pipeline Position

Runs after Verification Agent, before Consensus Evaluator.
