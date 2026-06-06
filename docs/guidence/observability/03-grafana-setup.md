# Step 3 — Grafana Setup (Beginner)

Grafana **visualizes** metrics from Prometheus. You can run Grafana locally (Docker) or use **Grafana Cloud free tier**.

**Free account:** [Grafana Cloud sign-up](https://grafana.com/auth/sign-up/create-user?pg=pricing&plcmt=free&cta=create-free-account)

---

## Choose your path

| Path | Best for | Difficulty |
|------|----------|------------|
| **A — Local Grafana (Docker)** | Week 1 kickoff, matches our compose file | Easy |
| **B — Grafana Cloud free** | No local Grafana container; cloud dashboards | Medium |

---

## Path A — Local Grafana (recommended for kickoff)

### 1. Start the full observability stack

If you followed [02-prometheus-setup.md](./02-prometheus-setup.md) Option A, Grafana is included:

```bash
cd docs/guidence/observability
cp observability.env.example .env
# Edit .env — set GRAFANA_ADMIN_PASSWORD to something secure
docker compose -f docker-compose.observability.yml up -d
```

### 2. Log in

1. Open **http://localhost:3000**
2. Username: `admin` (or value of `GRAFANA_ADMIN_USER` in `.env`)
3. Password: value of `GRAFANA_ADMIN_PASSWORD` in `.env`

On first login Grafana may ask you to change the password.

### 3. Confirm Prometheus datasource

Our compose file auto-provisions a datasource. Check:

1. **Connections → Data sources**
2. **Prometheus** should exist with URL `http://prometheus:9090`
3. Click **Save & test** — should show “Successfully queried the Prometheus API”

If missing, add manually:

| Field | Value |
|-------|-------|
| Name | Prometheus |
| URL | `http://prometheus:9090` (inside Docker) or `http://host.docker.internal:9090` (Grafana on host) |
| Access | Server |

### 4. Import the SLO dashboard

1. **Dashboards → New → Import**
2. Click **Upload JSON file**
3. Select `infrastructure/monitoring/grafana-slo-dashboard.json` from the repo root
4. Select **Prometheus** as the datasource
5. Click **Import**

You should see panels for availability, latency P95, and error rate (may show “No data” until traffic exists).

### 5. Create a “Guardrail violations” panel (Week 1 prep)

After Day 1 implementation, this metric will exist. Add a panel now as a placeholder:

1. **Dashboards → New dashboard → Add visualization**
2. Query:

```promql
sum by (agent_id, violation_type) (rate(guardrail_violations_total[5m]))
```

3. Title: **Guardrail violations (drift detection)**
4. Save dashboard as **Week 1 — Consensus & Drift**

---

## Path B — Grafana Cloud free tier

### 1. Create account

1. Go to [Grafana Cloud free sign-up](https://grafana.com/auth/sign-up/create-user?pg=pricing&plcmt=free&cta=create-free-account)
2. Complete registration and create a stack (e.g. `daily-briefing-dev`)
3. Note your stack URL: `https://YOUR-STACK.grafana.net`

### 2. Send metrics to Grafana Cloud (two sub-options)

**B1 — Grafana Alloy / Agent scraping local Prometheus (advanced)**  
Run Grafana Alloy on your machine to scrape `localhost:8010/metrics` and remote-write to Grafana Cloud. See [Grafana Cloud Prometheus docs](https://grafana.com/docs/grafana-cloud/).

**B2 — Keep local Prometheus + add Cloud datasource (simpler for kickoff)**  
1. Run local Prometheus per [02-prometheus-setup.md](./02-prometheus-setup.md)
2. In Grafana Cloud: **Connections → Data sources → Add Prometheus**
3. If Prometheus is only on localhost, use **Grafana Alloy** or expose Prometheus via secure tunnel — for Week 1 kickoff, **Path A (local Grafana)** is simpler.

> **Recommendation:** Use Path A for Week 1. Migrate to Grafana Cloud before production.

### 3. Import dashboard on Cloud

Same as Path A step 4 — upload `infrastructure/monitoring/grafana-slo-dashboard.json`.

### 4. Save Cloud credentials (optional)

For CI or provisioning later, store in `.env` (do not commit real values):

```bash
GRAFANA_CLOUD_STACK_URL=https://YOUR-STACK.grafana.net
GRAFANA_CLOUD_API_TOKEN=glsa_xxxxxxxx  # Service account token from Grafana Cloud
```

---

## Useful queries for Week 1

| Panel | PromQL |
|-------|--------|
| Security violations | `sum(rate(security_violations_total[5m])) by (type)` |
| Agent latency P95 | `histogram_quantile(0.95, sum(rate(agent_execution_duration_seconds_bucket[5m])) by (le, agent_id))` |
| DLQ growth | `increase(dlq_events_total[30m])` |
| Guardrail drift (Day 1+) | `sum(rate(guardrail_violations_total[5m])) by (agent_id, severity)` |

---

## Next step

→ [04-pagerduty-setup.md](./04-pagerduty-setup.md) — route Prometheus alerts to PagerDuty
