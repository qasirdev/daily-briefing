# Focus Agent

## Role
Planner — synthesizes tasks and calendar context into a time-blocked focus plan via LLM.

## Input
Task and calendar agent results from graph state.

## Output
`AgentResultEnvelope` with structured JSON plan (not markdown).

## Security Constraints
- Instruction hierarchy: system/guardrails override user data in `<user_data>` blocks
- Token budget enforced with escalation at 2x limit
