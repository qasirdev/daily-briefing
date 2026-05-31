# Calendar Agent

## Role
Doer — fetches today's calendar events via Google Calendar MCP.

## Input
`BriefingGraphState` with `user_id`, `trace_id`, optional `target_date`.

## Output
`AgentResultEnvelope` with structured `events` list.

## Security Constraints
- Read-only calendar access
- Escalates with `consent_required` when OAuth token expired
- Returns JSON only
