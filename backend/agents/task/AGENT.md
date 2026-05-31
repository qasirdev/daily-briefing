# Task Agent

## Role
Doer — fetches and prioritizes pending tasks from PostgreSQL MCP.

## Input
`BriefingGraphState` with `user_id`, `trace_id`.

## Output
`AgentResultEnvelope` with `result.tasks` sorted by priority and due date.

## Security Constraints
- Read-only MCP access
- All queries scoped by `user_id` (RLS)
- Returns JSON only — no user-facing markdown
