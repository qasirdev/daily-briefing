# Critic Agent

## Role

Quality and safety reviewer for the briefing pipeline. Scans external data for prompt injection, evaluates Focus Agent output, and drives a maximum two-cycle revision loop.

## Input

- `BriefingGraphState` with `task_result`, `calendar_result`, `focus_result`, `revision_count`, `trace_id`

## Output

- `AgentResultEnvelope` with:
  - `approved: bool`
  - `revision_required: bool`
  - `issues: list[str]`
  - `review_cycle: int`

## Security Constraints

- All external text (task titles, event summaries, focus plan fields) must pass `PromptInjectionDetector` before approval.
- Injection detections escalate immediately with `security_violation_detected` — no retries.
- Never emit user-facing markdown; JSON only.

## Revision Loop

- Max 2 revision cycles (`revision_count` in graph state).
- First pass approval returns immediately.
- After max revisions: accept with warning (`approved: true`, issues noted) unless security-related.
