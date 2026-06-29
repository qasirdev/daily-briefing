# Security Agent Context

**Version:** 2.0.0  
**Last Updated:** 2026-06-10

## Why This Agent Exists

The Security prompt pack documents threat models and classification rules shared across the multi-agent pipeline. Calendar events, task titles, and MCP responses are untrusted and may contain embedded instructions designed to manipulate downstream LLMs.

## Pipeline Position

```
External MCP data → Spotlighting → Input scanner → Agent LLM → Constitutional output scan → Critic
```

Security rules apply at every boundary — not only at a single node.

## User Need

Users need briefings generated safely without injection, exfiltration, or policy bypass. Security classification must be consistent so DLQ routing and audit logs are actionable.

## Gap Coverage

- Gap #114: Spotlighting for indirect injection
- Gap #126: Constitutional classifiers
- Gap #117: Tool poisoning defense vocabulary
