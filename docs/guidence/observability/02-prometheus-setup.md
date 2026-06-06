# Step 2 — Prometheus Setup (Beginner)

Prometheus **collects metrics** from your app by scraping `http://localhost:8010/metrics` every 15 seconds. It is **free open-source software** — there is no account signup. You run it locally (we use Docker).

**Official docs:** [Prometheus Installation](https://prometheus.io/docs/prometheus/latest/installation/)

---

## Prerequisites

- Docker Desktop installed and running
- Backend running locally (or ready to start):

```bash
cd /path/to/daily-briefing
nvm use 22          # Calendar MCP requires Node 22+
uv sync
uv run uvicorn backend.main:app --host 0.0.0.0 --port 8010 --reload
```

Verify metrics exist **before** starting Prometheus:

```bash
curl -s http://localhost:8010/metrics | head -20
```

You should see lines like `briefing_generation_duration_seconds` and `# HELP` comments.

---

## Option A — Docker Compose (recommended)

Uses the stack in this folder (Prometheus + Alertmanager + Grafana together).

```bash
cd docs/guidence/observability
cp observability.env.example .env
docker compose -f docker-compose.observability.yml up -d prometheus
```

Skip to [Verify Prometheus](#verify-prometheus) below.

---

## Option B — Prometheus only (manual Docker)

### 1. Create config directory

```bash
mkdir -p ~/prometheus-config
cp docs/guidence/observability/config/prometheus.yml ~/prometheus-config/
```

### 2. Edit scrape target if needed

Open `~/prometheus-config/prometheus.yml`. Default target:

```yaml
- targets: ['host.docker.internal:8010']
```

| How you run the app | Change target to |
|---------------------|------------------|
| `uvicorn` on Mac/Windows Docker | `host.docker.internal:8010` |
| `uvicorn` on Linux Docker | `172.17.0.1:8010` or host IP |
| Docker app on port 8088 | `host.docker.internal:8088` |

### 3. Start Prometheus

```bash
docker volume create prometheus-data

docker run -d \
  --name prometheus \
  -p 9090:9090 \
  -v ~/prometheus-config/prometheus.yml:/etc/prometheus/prometheus.yml \
  -v prometheus-data:/prometheus \
  prom/prometheus:latest \
  --config.file=/etc/prometheus/prometheus.yml \
  --storage.tsdb.path=/prometheus \
  --web.enable-lifecycle
```

Also mount alert rules if you want alerting in this container:

```bash
# Add these volume mounts:
-v /path/to/daily-briefing/infrastructure/monitoring/recording_rules.yml:/etc/prometheus/recording_rules.yml \
-v /path/to/daily-briefing/infrastructure/alerting/rules.yml:/etc/prometheus/alert_rules.yml \
```

---

## Verify Prometheus

### 1. Open the UI

Visit **http://localhost:9090**

### 2. Check the scrape target

1. Go to **Status → Targets**
2. Find job `daily-briefing`
3. State should be **UP** (green)

If **DOWN**:

- Confirm backend is running on port 8010
- On Linux, replace `host.docker.internal` with your host IP in `prometheus.yml`
- Restart Prometheus after config changes

### 3. Run a test query

In **Graph** tab, enter:

```promql
security_violations_total
```

Click **Execute**. Empty result is OK before traffic — the metric exists once the app has started.

After generating a briefing or running tests:

```promql
rate(briefing_generation_duration_seconds_count[5m])
```

### 4. Confirm alert rules loaded (optional)

**Status → Rules** should list groups from `infrastructure/alerting/rules.yml` when using our Docker Compose config.

---

## What Prometheus stores

Prometheus keeps time-series data in its volume (`prometheus-data`). Data persists across container restarts but is **local dev only** — not for production long-term storage without additional setup.

---

## Next step

→ [03-grafana-setup.md](./03-grafana-setup.md) — visualize metrics and import the SLO dashboard
