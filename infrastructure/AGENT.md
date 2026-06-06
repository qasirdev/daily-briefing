# Infrastructure Agent

**Version:** 1.7.0 | **Last Updated:** May 2026

## Scope

CI/CD, GitHub branch policy, container signing, alerting runbooks, and deployment rules.

---

## GitHub Branch Policy

| Branch | Purpose |
|---|---|
| `epic/autonomus-implementation` | Long-lived integration branch — all epics merge here |
| `epic/E{n}-{short-description}` | Short-lived per-epic work branch |
| `main` | Not used for epic merges during autonomous implementation |

### Epic-to-Epic Flow

1. Branch from latest `epic/autonomus-implementation`
2. Push `epic/E{n}-...`; implement → refactor → test → docs
3. Open PR with base `epic/autonomus-implementation`
4. Merge with a **merge commit** after CI passes (not squash or rebase)
5. Pull integration branch; delete **local** epic branch
6. **Do not** delete the remote epic branch on GitHub
7. Start next epic from updated `epic/autonomus-implementation`

---

## CI Workflows

| Workflow | Trigger | Purpose |
|---|---|---|
| `.github/workflows/ci.yml` | PR + push to integration | Lint, typecheck, AI-BOM validation, pip-audit, unit/e2e tests, docker build |
| `.github/workflows/docker-publish.yml` | Push to integration + tags | Build, push GHCR, Cosign sign/verify |

---

## Cosign Image Verification

After `docker-publish` completes:

```bash
cosign verify \
  --certificate-identity-regexp='.*' \
  --certificate-oidc-issuer='https://token.actions.githubusercontent.com' \
  ghcr.io/qasirdev/daily-briefing@sha256:<digest>
```

Unsigned images must be rejected in production environments.

---

## Alert Runbooks

### HighErrorRate

1. Check `/metrics` for `briefing_generation_duration_seconds` failure rate.
2. Inspect DLQ admin API for recent escalations.
3. Roll back latest deployment if error spike correlates with release.

### SecurityViolationSpike

1. Query security logs for `prompt_injection_detected` / `ssrf_blocked`.
2. Review DLQ entries with `security_violation_detected`.
3. Block offending calendar sources if repeated.

### HighLatency

1. Check MCP and LLM provider latency metrics.
2. Verify token budget utilization gauges.
3. Scale workers if CPU-saturated.

### DLQGrowing

1. List DLQ events via admin API.
2. Identify dominant `reason` label.
3. Fix upstream MCP/LLM failures before mass retry.

### LocalLLMFallback

1. Confirm OpenRouter availability and quota.
2. Validate local LLM endpoint health.
3. Adjust routing only after provider recovery.

---

## Deployment Reference

See `infrastructure/DEPLOYMENT.md` for step-by-step production deployment, rollback, and monitoring setup.

**Local observability:** See `docs/guidence/observability/README.md` for Prometheus, Grafana, and PagerDuty setup before Week 1 kickoff.

---

*Infrastructure Agent — Version 1.7.0 — May 2026*
