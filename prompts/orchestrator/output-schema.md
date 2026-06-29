# Orchestrator Agent Output Schema

**Version:** 2.0.0

Emit **pure JSON only** (no markdown fences). Wrap in `AgentResultEnvelope`:

```json
{
  "agent_id": "orchestrator",
  "canonical_role": "supervisor",
  "status": "success|failure|escalated",
  "result": {
    "primary_payload": "briefing markdown synthesized from sub-agent JSON"
  },
  "metadata": {
    "prompt_version": "v2.0.0",
    "spotlighting_applied": true
  }
}
```
