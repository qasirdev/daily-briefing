# Adversarial Agent Contract

## Version
v1.1.0

## Canonical Role
Adversarial (Red Team)

## Token Budget
| Direction | Budget | Hard Limit |
|---|---|---|
| Input | 14000 | 28000 |
| Output | 2500 | 5000 |

## Security Constraints
- Read-only analysis — no MCP mutations
- JSON output only
- Internal adversarial reasoning must not leak to users

## Integration
- **Upstream:** Focus Agent, Verification Agent, MCP envelopes
- **Downstream:** Consensus Evaluator
- **Envelope:** `AgentResultEnvelope` with `canonical_role="adversarial"`
