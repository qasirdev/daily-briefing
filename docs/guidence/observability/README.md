# Observability Setup — Beginner Guide

Step-by-step guides for **Prometheus**, **Grafana**, and **PagerDuty** before Week 1 gap remediation kickoff.

**Project context:** The Daily Briefing app exposes Prometheus metrics at `/metrics` (see [docs/OBSERVABILITY.md](../../OBSERVABILITY.md)). Alert rules live in [infrastructure/alerting/rules.yml](../../../infrastructure/alerting/rules.yml). Week 1 Day 1 adds `guardrail_violations_total` — you need Prometheus scraping the app to verify that work.

---

## What to set up before kickoff

| Tool | Required before Day 1? | Why |
|------|------------------------|-----|
| **Prometheus** | **Yes** | Day 1 acceptance criteria: metrics visible and scraped; tests verify real counters |
| **Grafana** | **Recommended** | Week 1 guide: import SLO dashboard; visualize drift metrics as you build |
| **PagerDuty** | **Before Day 1 end** | Week 1 guide: configure alert routing; test one alert fires to PagerDuty |

You do **not** need a paid account for local development:

| Tool | Cost model | Sign-up / install |
|------|------------|-------------------|
| Prometheus | Free, self-hosted | [Prometheus installation docs](https://prometheus.io/docs/prometheus/latest/installation/) — we use Docker (easiest) |
| Grafana | Free tier (Grafana Cloud) **or** local Docker | [Grafana Cloud free account](https://grafana.com/auth/sign-up/create-user?pg=pricing&plcmt=free&cta=create-free-account) |
| PagerDuty | Free trial / developer plan | [PagerDuty](https://www.pagerduty.com/) — Start for Free |

---

## Recommended order (≈ 60–90 minutes)

1. **[01-prerequisites.md](./01-prerequisites.md)** — Docker, Node 22, backend running
2. **[02-prometheus-setup.md](./02-prometheus-setup.md)** — scrape the app at `http://localhost:8010/metrics`
3. **[03-grafana-setup.md](./03-grafana-setup.md)** — connect Grafana to Prometheus; import SLO dashboard
4. **[04-pagerduty-setup.md](./04-pagerduty-setup.md)** — Events API v2 key → Alertmanager → test alert
5. **[05-verify-before-kickoff.md](./05-verify-before-kickoff.md)** — checklist before running KICKOFF-PROMPT Day 1

### Fast path: one Docker Compose command

If you prefer one command instead of three separate guides:

```bash
cd docs/guidence/observability
cp observability.env.example .env
# docker compose -f docker-compose.observability.yml down
# docker rm -f briefing-alertmanager briefing-grafana briefing-prometheus 2>/dev/null

# Edit .env — set PAGERDUTY_ROUTING_KEY after PagerDuty setup (step 3)
docker compose -f docker-compose.observability.yml up -d
```

Then follow [05-verify-before-kickoff.md](./05-verify-before-kickoff.md).

---

## Architecture (local dev)

```
┌─────────────────────┐     scrape /metrics      ┌──────────────┐
│  FastAPI :8010      │ ───────────────────────► │ Prometheus   │
│  (uv run uvicorn)   │                          │ :9090        │
└─────────────────────┘                          └──────┬───────┘
                                                        │ evaluate rules
                                                        ▼
                                                 ┌──────────────┐
                                                 │ Alertmanager │
                                                 │ :9093        │
                                                 └──────┬───────┘
                                                        │ Events API v2
                                                        ▼
                                                 ┌──────────────┐
                                                 │ PagerDuty    │
                                                 └──────────────┘

┌──────────────┐     query Prometheus API
│ Grafana      │ ◄──────────────────────────── Prometheus :9090
│ :3000        │
└──────────────┘
```

**Ports used (defaults):**

| Service | URL |
|---------|-----|
| App metrics | http://localhost:8010/metrics |
| Prometheus UI | http://localhost:9090 |
| Alertmanager UI | http://localhost:9093 |
| Grafana UI | http://localhost:3000 |

---

## Environment variables

### Application (`.env`)

The FastAPI app only needs **OpenTelemetry** today; metrics are exposed in-process via `prometheus_client` at `/metrics`.

| Variable | Required | Description |
|----------|----------|-------------|
| `OTEL_EXPORTER_OTLP_ENDPOINT` | Optional | OTLP collector for traces (default `http://localhost:4317`) |
| `ADMIN_API_KEY` | Optional dev | For DLQ admin API during incident debugging |

See updated sections in `.env.example` and `.env.production.example`.

### Observability stack (`docs/guidence/observability/.env`)

Copy from [observability.env.example](./observability.env.example). Used by Docker Compose for Alertmanager and Grafana — **not** read by the Python app.

| Variable | Required | Description |
|----------|----------|-------------|
| `PAGERDUTY_ROUTING_KEY` | For alerts | Events API v2 integration key from PagerDuty |
| `GRAFANA_ADMIN_USER` | Local Grafana | Default `admin` |
| `GRAFANA_ADMIN_PASSWORD` | Local Grafana | Change from default |
| `APP_METRICS_TARGET` | Prometheus scrape | Default `host.docker.internal:8010` (Mac/Windows Docker) |

---

## Related project files

| File | Purpose |
|------|---------|
| [infrastructure/alerting/rules.yml](../../../infrastructure/alerting/rules.yml) | Production alert definitions |
| [infrastructure/monitoring/recording_rules.yml](../../../infrastructure/monitoring/recording_rules.yml) | SLO recording rules |
| [infrastructure/monitoring/grafana-slo-dashboard.json](../../../infrastructure/monitoring/grafana-slo-dashboard.json) | Dashboard to import |
| [docs/gaps/KICKOFF-PROMPT.md](../../gaps/KICKOFF-PROMPT.md) | Week 1 kickoff (run after this setup) |

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Prometheus shows target **DOWN** | **Docker app:** set `APP_METRICS_TARGET=host.docker.internal:8088` in `observability/.env`, rebuild app (`docker compose build app && docker compose up -d`), restart Prometheus. **Local uvicorn:** `uv run uvicorn backend.main:app --host 0.0.0.0 --port 8010` and use `APP_METRICS_TARGET=host.docker.internal:8010` |
| Target DOWN with `503 Server shutting down` | Stale uvicorn on host :8010 — `lsof -i :8010` then `kill <pid>` and restart backend, or switch scrape target to Docker `:8088` |
| Empty metrics in Prometheus | Generate traffic: `curl http://localhost:8088/health` (Docker) or `:8010/health` (uvicorn), then check `/metrics/` |
| SLO dashboard "No data" | Recording rules need briefing traffic — run at least one briefing via the UI or `POST /api/v1/briefing` |
| Docker cannot reach app on Mac | Use `host.docker.internal` in `APP_METRICS_TARGET` (see `observability.env.example`) |
| PagerDuty test alert not received | Confirm `PAGERDUTY_ROUTING_KEY` in `observability/.env` and restart Alertmanager |
| Alertmanager restart loop (no PagerDuty key) | Expected when key is empty — stack uses `alertmanager.no-pagerduty.yml`; set key in `.env` for real routing |
| Grafana `exec /run.sh: exec format error` | Corrupted `latest` image — run `docker rmi grafana/grafana:latest` then `docker compose pull grafana` (compose pins `grafana/grafana:11.5.2`) |
| Grafana “No data” | Check Prometheus datasource URL is `http://prometheus:9090` (inside Docker network) |

---

*Observability setup guide — June 2026*
