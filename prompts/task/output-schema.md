# Task Agent Output Schema

**Version:** 2.0.0

Emit **pure JSON only** (no markdown fences). Wrap in `AgentResultEnvelope`:

```json
{
  "agent_id": "task",
  "canonical_role": "doer",
  "status": "success|failure|escalated",
  "result": {
    "primary_payload": "tasks array with title, priority, due_date, status"
  },
  "metadata": {
    "prompt_version": "v2.0.0",
    "spotlighting_applied": true
  }
}
```
