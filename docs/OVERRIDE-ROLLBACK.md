# Override & Rollback Procedures

**Gaps #68, #95** | **Week 7 (DB-E14)**

Clear paths for humans to pause, override, or rollback agent behavior.

---

## User Override Paths

| Action | Trigger | Effect |
|---|---|---|
| **Deny consent** | Consent modal — "Deny" | Briefing aborts; no MCP credentials issued |
| **Revoke consent** | Settings page | Active consent invalidated immediately; per-action authz denies next call |
| **Shorter TTL** | Consent modal TTL selector | Limits standing permission window |

Per-action authorization ensures revoked consent takes effect on the **next** MCP call — no stale session cache beyond credential TTL (≤900s).

---

## Operator Override Paths

| Action | Trigger | Effect |
|---|---|---|
| **Human escalation** | Consensus `major_concerns >= 2` | Graph status `awaiting_human_review`; Orchestrator does not present |
| **Circuit breaker** | Token budget ≥2× limit | Agent routed to DLQ |
| **Memory quarantine** | Drift or poisoning detection | Affected memory layer isolated |
| **Emergency hotfix** | P1 incident | Tier 1 deploy per `docs/GOVERNANCE.md` |

---

## Rollback Procedures

### Prompt Rollback

1. Identify last known-good git tag from red team baseline
2. Revert `prompts/{agent}/` to tagged version
3. Run `test_jailbreak_corpus.py` — confirm ≥95% block rate
4. Deploy via standard pipeline (or Tier 1 if active exploit)

### Configuration Rollback

1. Revert `backend/settings.py` / env changes
2. Restart supervisord processes
3. Verify audit chain intact: `verify_audit_chain()`

### Consent / Credential Rollback

1. Bulk revoke via consent API for affected `user_id`
2. Clear broker in-memory cache (`CredentialBroker._cache`)
3. Confirm `per_action_authz_total{outcome="deny"}` increments on retry

---

## Reasoning-Level Feedback

Users rate individual agent reasoning steps via `ReasoningFeedback` on the briefing page. Ratings (`correct`, `partial`, `incorrect`) POST to `/api/v1/feedback/reasoning` and persist as episodic lessons with `feedback_type=reasoning_feedback`.

Output-level preference edits remain on `/api/v1/preferences/feedback`.

Current: operators review `reasoning_trace` in API response and frontend `ReasoningTrace` component.

---

*Override & Rollback — Week 7 Gap Remediation*
