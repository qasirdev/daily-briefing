# Security Policy

## Supported Versions

| Version | Supported |
|---|---|
| 0.1.x | ✅ Active development |

## Reporting a Vulnerability

Report security issues privately via GitHub Security Advisories on this repository.
Do not open public issues for undisclosed vulnerabilities.

Include:

- Affected component (backend, frontend, MCP integration)
- Reproduction steps
- Impact assessment

We aim to acknowledge reports within 48 hours.

## Supply Chain Controls

- **pip-audit** runs in CI and blocks critical/high CVEs in production dependencies.
- **OpenSSF Scorecard** minimum threshold: **7.0/10** (manual weekly run documented in `docs/SUPPLY-CHAIN-SECURITY.md`).
- **AI-BOM** manifest: `infrastructure/ai-bom.yaml` — validated on every CI run.
- **Container images** are Cosign-signed via `.github/workflows/docker-publish.yml`.

## Security Documentation

Full architecture and controls: [`docs/SECURITY.md`](docs/SECURITY.md)

When extending the OWASP injection regression corpus, update payload/pattern counts in all
tracked docs (see **Regression corpus inventory** in `docs/SECURITY.md` and
`backend/tests/security/test_corpus_inventory.py`).

When adding or removing pytest cases, update total test counts in all tracked docs
(see **Test suite inventory** in `docs/SECURITY.md` and
`backend/tests/test_suite_inventory.py`).
