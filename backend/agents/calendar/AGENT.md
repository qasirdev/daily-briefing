# Calendar Agent

## Role
Doer — fetches today's calendar events via Google Calendar MCP.

## Input
`BriefingGraphState` with `user_id`, `trace_id`, optional `target_date`.

## Output
`AgentResultEnvelope` with structured `events` list.

Event `start` and `end` use British formatting (Europe/London):
- Timed: `DD-MM-YYYY at HH:MM` (e.g. `31-05-2026 at 22:00`)
- All-day: `DD-MM-YYYY`

## Security Constraints
- Read-only calendar access
- Escalates with `consent_required` when OAuth token expired
- Returns JSON only
