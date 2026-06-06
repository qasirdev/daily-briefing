# Week 5 Learning — Supply Chain Security & JIT Credentials

**Epic:** DB-E12 | **Date:** 2026-06-06

---

## What We Built

1. **AI-BOM** (`infrastructure/ai-bom.yaml`) — models, embeddings, libraries, MCP servers with CI validation.
2. **Supply chain CI** — `pip-audit` blocks critical/high CVEs; OpenSSF Scorecard ≥7.0 documented for manual runs.
3. **Sealed audit log** — SHA-256 hash chain in `backend/security/audit.py`; consent grants append automatically.
4. **JIT CredentialBroker** — consent-gated issuance with TTL cache and `credential_issuance_total` metric.
5. **Calendar MCP mediation** — broker resolves env per tool call instead of constructor-time refresh token.

---

## Key Patterns

### Hash-chain audit entries

```
entry_hash = sha256(prev_hash + canonical_json(entry_without_hash))
genesis = "0" * 64
```

Only `payload_hash` is stored — never raw PII or tokens.

### Broker cache key

```
{user_id}:{service}:{intent}
```

Single audit entry per TTL window (idempotent issuance).

### BOM validation

Runtime `Settings` model names must appear in `ai-bom.yaml` `models` section; embedding model must appear in `embeddings`.

---

## Files Added

| File | Purpose |
|---|---|
| `backend/security/bom.py` | AI-BOM loader/validator |
| `backend/security/audit.py` | Sealed audit log writer |
| `backend/security/vault.py` | JIT credential broker |
| `scripts/validate_ai_bom.py` | CI validation CLI |
| `docs/SUPPLY-CHAIN-SECURITY.md` | Policy + vendor table |

---

## Verification

```bash
uv run python scripts/validate_ai_bom.py
uv run ruff check backend
uv run mypy backend
uv run pytest backend/tests/security/test_ai_bom.py \
  backend/tests/security/test_audit_sealing.py \
  backend/tests/security/test_vault.py \
  backend/tests/security/test_supply_chain_integration.py -v
```

---

## Future Work

- Persist audit log writer to PostgreSQL `audit_log` table at runtime
- Redis-backed credential cache for multi-worker deployments
- Automated OpenSSF Scorecard in scheduled GitHub Action
