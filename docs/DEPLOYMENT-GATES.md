# Deployment Gates — Metric-Based Release Criteria

**Gap #59** | **Week 8 (DB-E139)** | **Last updated:** 2026-06-08

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

## Production prerequisites

`check_deployment_gates()` calls `get_settings()`, which loads `.env` and validates production secrets when `APP_ENV=production`. The gate check fails **before** metrics are evaluated if these are missing or insecure.

| Variable | Requirement |
|---|---|
| `JWT_SECRET_KEY` | ≥ 32 characters; must not contain `dev-only` or `change-me-in-production` |
| `ADMIN_API_KEY` | Non-empty |
| `APP_DEBUG` | `false` |
| `OPENROUTER_API_KEY` | Required when `LOCAL_LLM_ENABLED=false` |

Generate a secure JWT secret:

```bash
openssl rand -hex 32
```

See `.env.production.example` for the full production variable set.

---

## Evaluation

### Local development (metrics only)

Omit `APP_ENV=production`. Failed gates downgrade to `warn` (`warn_only=True`):

```bash
uv run python -c "from backend.observability.deployment_gates import check_deployment_gates; print(check_deployment_gates())"
```

### Production mode (release check)

Override production secrets on the command line or use a production `.env`:

```bash
APP_ENV=production \
JWT_SECRET_KEY="$(openssl rand -hex 32)" \
ADMIN_API_KEY="your-admin-key" \
APP_DEBUG=false \
LOCAL_LLM_ENABLED=true \
uv run python -c "
from backend.observability.deployment_gates import check_deployment_gates
report = check_deployment_gates()
assert report.all_pass, report
print('All gates passed:', report)
"
```

**Production mode:** Any `fail` status blocks deployment until remediated (`warn_only=False`).

---

## CI integration

Enforced in `.github/workflows/docker-publish.yml` **before** image build and push:

1. Sync Python dependencies
2. Evaluate `check_deployment_gates()` with `APP_ENV=production`
3. Require `all_pass=True` — workflow exits non-zero on failure
4. Build, push, and sign the image only if gates pass

CI uses workflow-scoped placeholder secrets that satisfy `Settings` validation; real deployment secrets are injected at runtime via your hosting platform (Key Vault, GitHub Actions secrets, etc.).

---

## Related Documentation

- `docs/GOVERNANCE.md` — emergency change tiers
- `docs/OBSERVABILITY.md` — SLO definitions
- `docs/security/MITRE-ATTACK-COVERAGE.md`
- `docs/gaps/production/PROD-GAP-ANALYSIS-REVIEW.md` — PROD-004

---

*Deployment Gates — Week 8 Gap Remediation*
