# Pre-Kickoff Verification Checklist

Complete this checklist **before** running [KICKOFF-PROMPT Day 1](../../gaps/KICKOFF-PROMPT.md).

---

## 1. Environment

```bash
nvm use 22
python3 --version    # 3.12+
uv sync
uv run pytest -v     # baseline: all tests pass
```

- [ ] Node.js 22+ active (`node --version`)
- [ ] Python 3.12+ in uv venv
- [ ] Baseline tests pass

---

## 2. MCP (already verified in planning session)

```bash
LIVE_STDIO_E2E=1 uv run pytest backend/tests/integration/test_live_stdio_briefing.py -v
```

- [ ] PostgreSQL MCP live test passes
- [ ] Calendar MCP works (optional quick check via app or calendar stdio client)

---

## 3. Application metrics endpoint

```bash
# Terminal 1 — start backend
uv run uvicorn backend.main:app --host 0.0.0.0 --port 8010 --reload

# Terminal 2 — verify
curl -sf http://localhost:8010/health
curl -sf http://localhost:8010/metrics | grep -E 'briefing_generation|security_violations'
```

- [ ] `/health` returns 200
- [ ] `/metrics` returns Prometheus text format with app metrics

---

## 4. Prometheus

```bash
cd docs/guidence/observability
docker compose -f docker-compose.observability.yml ps
```

Open http://localhost:9090 → **Status → Targets** → `daily-briefing` is **UP**

- [ ] Prometheus container running
- [ ] Scrape target UP
- [ ] Query `security_violations_total` executes (empty OK)

---

## 5. Grafana

Open http://localhost:3000 → log in

- [ ] Grafana accessible
- [ ] Prometheus datasource connected (Save & test OK)
- [ ] SLO dashboard imported from `infrastructure/monitoring/grafana-slo-dashboard.json`

---

## 6. PagerDuty + Alertmanager

```bash
# Send test alert (macOS)
curl -X POST http://localhost:9093/api/v2/alerts \
  -H 'Content-Type: application/json' \
  -d '[{
    "labels": {"alertname":"KickoffTest","severity":"critical"},
    "annotations": {"summary":"Pre-kickoff PagerDuty test"},
    "startsAt": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'"
  }]'
```

- [ ] Alertmanager running (http://localhost:9093)
- [ ] PagerDuty incident created from test alert
- [ ] Incident acknowledged and resolved

---

## 7. Git & planning

```bash
git checkout epic/autonomus-implementation-gap
git pull origin epic/autonomus-implementation-gap
git checkout -b epic/week1-gap-remediation
```

- [ ] On branch `epic/week1-gap-remediation`
- [ ] `docs/tasks/todo.md` updated with Week 1 plan
- [ ] `ENABLE_CONSENSUS_WORKFLOW=false` in `.env`
- [ ] `logs/` directory exists

---

## 8. Mandatory reading (skim minimum)

- [ ] `AGENT.md`
- [ ] `docs/EXECUTION-RULES.md`
- [ ] `docs/gaps/WEEK1-IMPLEMENTATION-GUIDE.md` — Day 1 section
- [ ] `docs/example-code/examples/2026-12-01-youtube-IBM.md` — consensus model context

---

## All green?

Reply **proceed** in Cursor to start **Day 1: Drift Detection & Observability**.

Expected Day 1 deliverables:

- `GuardrailViolation` in `backend/schemas/envelope.py`
- `backend/observability/metrics.py` (consolidated metrics)
- `backend/tests/observability/test_drift_detection.py` (7 tests)
- Prometheus shows `guardrail_violations_total` after tests run
