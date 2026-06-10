# Supply Chain Security

**Version:** 1.0.0 | **Last Updated:** June 2026 | **Owner:** platform-security

---

## AI Bill of Materials (AI-BOM) — Gap #115

**Manifest:** `infrastructure/ai-bom.yaml`

Tracks provenance for:

- LLM models (OpenRouter primary + local fallback)
- Embedding models
- Critical Python libraries
- MCP server packages

**Update cadence:** Weekly (automated validation on every CI run)

**Validation:**

```bash
uv run python scripts/validate_ai_bom.py
```

**Stale BOM policy:** Warn when `metadata.last_updated` is >7 days old; warn-only in CI (does not block merge).

---

## OpenSSF Scorecard — Gap #116

**Minimum overall score:** ≥7.0/10

**Required practices:**

| Check | Requirement |
|---|---|
| Security Policy | `SECURITY.md` at repo root |
| Dependency updates | Dependabot / Renovate |
| Code review | Required for all PRs |
| SAST | Ruff + Mypy + pytest in CI |

**Manual weekly run** (Scorecard CLI not in CI due to tooling/network constraints):

```bash
ossf-scorecard --repo=github.com/qasirdev/daily-briefing --format=json \
  > scorecard-results/scorecard.json
```

**Action on failure:**

- Score <7.0: manual security review required before merge
- Critical dependency CVE: block deployment (pip-audit gate)

---

## pip-audit CI Gate

CI runs `uv run pip-audit --desc on --ignore-vuln GHSA-rrmf-rvhw-rf47` on every PR. Blocks on **critical** and **high** severity CVEs in production dependencies.

**Pinned upgrades (2026-06):** `transformers>=5.0.0rc3` and `huggingface-hub>=1.5.0` resolve GHSA-69w3-r845-3855 and PYSEC-2025-217 (transitive via `llamafirewall`).

**Documented exception — `GHSA-rrmf-rvhw-rf47` (`torch`):** Local-only `torch.jit.script` issue with no fixed PyPI release ≤2.12.0. Ignored in CI because PromptGuard inference does not use JIT scripting or untrusted checkpoint loads. Tracked in `infrastructure/ai-bom.yaml` with expiry **2026-12-31**.

**Other transitive CVE with no fix:** Document exception in `docs/adr/` with expiry date.

**Dev-only dependencies:** Excluded from production audit scope (`pip-audit` scans installed runtime deps).

---

## Vendor Security Assessments — Gap #127

Re-assessment due every **6 months** or after a security incident.

| Vendor / Component | Type | Assessment Date | SOC 2 | ISO 27001 | Data Residency | FOSS License | Re-assess Due |
|---|---|---|---|---|---|---|---|
| OpenRouter | SaaS LLM | 2026-01-15 | Vendor-managed | Vendor-managed | US | N/A (Commercial API) | 2026-07-15 |
| Google Calendar API | SaaS | 2026-02-01 | Yes | Yes | US/EU (workspace config) | N/A | 2026-08-01 |
| `@franciscpd/calendar-mcp-server` | FOSS MCP | 2026-06-01 | N/A | N/A | Runs locally (stdio) | MIT | 2026-12-01 |
| `@modelcontextprotocol/server-postgres` | FOSS MCP | 2026-06-01 | N/A | N/A | Runs locally (stdio) | MIT | 2026-12-01 |
| Ollama (local LLM) | Self-hosted | N/A | N/A | N/A | On-prem | Llama Community | N/A |

**FOSS without vendor SOC 2:** Document source repository and last commit review date in ADR.

---

## Related Documentation

- `docs/adr/ADR-supply-chain-week5.md` — Week 5 architectural decisions
- `docs/SECURITY.md` — JIT credentials and cryptographic audit integrity
- `infrastructure/ai-bom.yaml` — Machine-readable BOM
