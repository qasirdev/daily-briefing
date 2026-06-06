# Deployment Gates — Metric-Based Release Criteria

**Gap #59** | **Week 8 (DB-E139)** | **Last updated:** 2026-06-06

Production deployments MUST pass metric-based gates before promotion. Gates are evaluated programmatically via `check_deployment_gates()`.

---

## Gates

| Gate ID | Name | Target | Source |
|---|---|---|---|
| `mitre_coverage` | MITRE ATT&CK Coverage | ≥ 0.80 | `get_coverage_summary()` |
| `alert_investigation` | Alert Investigation Coverage | ≥ 0.95 | `get_alert_investigation_coverage()` |
| `agentic_rag` | Agentic RAG Enabled | `true` | `Settings.enable_agentic_rag` |
| `context_compression` | Context Compression Budget | ≥ 4000 chars | `Settings.context_compression_max_chars` |

---

## Evaluation

```bash
uv run python -c "from backend.observability.deployment_gates import check_deployment_gates; print(check_deployment_gates())"
```

**Development mode:** Failed gates downgrade to `warn` status (`warn_only=True`).

**Production mode:** Any `fail` status blocks deployment until remediated.

---

## CI Integration

Add to release pipeline after test suite:

1. Run full pytest suite (must pass)
2. Evaluate `check_deployment_gates()` with `APP_ENV=production`
3. Require `all_pass=True` before image promotion

---

## Related Documentation

- `docs/GOVERNANCE.md` — emergency change tiers
- `docs/OBSERVABILITY.md` — SLO definitions
- `docs/security/MITRE-ATTACK-COVERAGE.md`

---

*Deployment Gates — Week 8 Gap Remediation*
