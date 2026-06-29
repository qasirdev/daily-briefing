# Calendar Agent Output Schema

**Version:** 2.0.0

Emit **pure JSON only** (no markdown fences). Wrap in `AgentResultEnvelope`:

```json
{
  "agent_id": "calendar",
  "canonical_role": "tool_operator",
  "status": "success|failure|escalated",
  "result": {
    "primary_payload": "events array with summary, start, end, attendees"
  },
  "metadata": {
    "prompt_version": "v2.0.0",
    "spotlighting_applied": true
  }
}
```
