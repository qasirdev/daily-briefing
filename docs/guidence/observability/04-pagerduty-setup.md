# Step 4 — PagerDuty Setup (Beginner)

PagerDuty receives **alerts** when Prometheus rules fire (via Alertmanager). Used for critical events like security violation spikes and high error rates — and Week 1 guardrail drift alerts.

**Sign up:** [PagerDuty — Start for Free](https://www.pagerduty.com/)

---

## Overview

```
Prometheus (rules) → Alertmanager → PagerDuty Events API v2 → On-call notification
```

The Python app does **not** call PagerDuty directly. Configuration lives in **Alertmanager**.

---

## Step 1 — Create a PagerDuty account

1. Go to [https://www.pagerduty.com/](https://www.pagerduty.com/)
2. Click **Start for Free** / **Start free trial**
3. Complete signup (email verification)
4. Create or join a **Team** when prompted

Free trial includes enough for development and Week 1 testing.

---

## Step 2 — Create a service

1. In PagerDuty: **Services → Service Directory → + New Service**
2. Settings:
   - **Name:** `Daily Briefing — Dev`
   - **Description:** Local/staging alerts for AI Daily Briefing Assistant
   - **Escalation Policy:** Default (assign yourself)
   - **Alert Grouping:** Intelligent
3. Click **Create Service**

---

## Step 3 — Add Events API v2 integration

1. Open your new service
2. Go to **Integrations** tab
3. Click **Add an integration**
4. Select **Events API V2**
5. Click **Add**
6. Copy the **Integration Key** (32-character hex string)

This key is your **`PAGERDUTY_ROUTING_KEY`**.

> Keep this secret — treat like a password. Do not commit to git.

---

## Step 4 — Configure Alertmanager

### Using our Docker Compose stack

1. Edit `docs/guidence/observability/.env`:

```bash
PAGERDUTY_ROUTING_KEY=your-integration-key-here
```

2. Restart Alertmanager:

```bash
cd docs/guidence/observability
docker compose -f docker-compose.observability.yml up -d alertmanager
```

Our `config/alertmanager.yml` template uses `${PAGERDUTY_ROUTING_KEY}` via envsubst at container start.

### Manual Alertmanager config

If running Alertmanager separately, add to `alertmanager.yml`:

```yaml
receivers:
  - name: pagerduty-critical
    pagerduty_configs:
      - routing_key: YOUR_INTEGRATION_KEY
        severity: '{{ .CommonLabels.severity }}'
        description: '{{ .CommonAnnotations.summary }}'
        client: daily-briefing-alertmanager
        client_url: 'http://localhost:9090/alerts'

route:
  receiver: pagerduty-critical
  group_by: ['alertname', 'severity']
  group_wait: 30s
  group_interval: 5m
  repeat_interval: 4h
  routes:
    - match:
        severity: info
      receiver: 'null'   # don't page for info-level
    - match:
        severity: warning
      receiver: pagerduty-critical
    - match:
        severity: critical
      receiver: pagerduty-critical

receivers:
  - name: 'null'
```

---

## Step 5 — Connect Prometheus to Alertmanager

Our Docker Compose config already sets:

```yaml
# prometheus.yml
alerting:
  alertmanagers:
    - static_configs:
        - targets: ['alertmanager:9093']
```

Verify in Prometheus UI: **Status → Alertmanager** should show **UP**.

---

## Step 6 — Test alert delivery

### Option A — Fire a test alert via Alertmanager API

```bash
curl -X POST http://localhost:9093/api/v2/alerts \
  -H 'Content-Type: application/json' \
  -d '[{
    "labels": {
      "alertname": "PagerDutyTest",
      "severity": "critical",
      "service": "daily-briefing"
    },
    "annotations": {
      "summary": "Test alert from observability setup guide"
    },
    "startsAt": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'",
    "endsAt": "'$(date -u -v+5M +%Y-%m-%dT%H:%M:%SZ 2>/dev/null || date -u -d '+5 minutes' +%Y-%m-%dT%H:%M:%SZ)'"
  }]'
```

> On macOS use `-v+5M`; on Linux use `-d '+5 minutes'`.

Within 1–2 minutes you should see an incident in PagerDuty and receive email/app notification.

### Option B — Trigger a real rule (after traffic)

Once the app has generated errors or security violations, rules in `infrastructure/alerting/rules.yml` may fire naturally. Example:

```promql
increase(security_violations_total[10m]) > 5
```

---

## Step 7 — Acknowledge and resolve in PagerDuty

1. Open the incident in PagerDuty web or mobile app
2. Click **Acknowledge** to confirm you received it
3. Click **Resolve** after testing

This completes the alert loop verification required by the Week 1 guide.

---

## Production notes

| Topic | Dev (Week 1) | Production |
|-------|--------------|------------|
| Integration key | One dev service | Separate prod service + key |
| Escalation | Default (you) | Team rotation policy |
| Info alerts | Suppressed in our route | Route to Slack, not PagerDuty |
| Secrets | `observability/.env` (gitignored) | Azure Key Vault / GitHub Secrets |

Store production key in `.env.production` on the server — see `.env.production.example`.

---

## Troubleshooting

### "Account Is Unavailable" at `your-subdomain.pagerduty.com/not_found`

This means PagerDuty cannot serve that account subdomain. Common causes:

| Cause | What to do |
|-------|------------|
| **Signup never completed** | Check email for a PagerDuty verification link; finish activation before using the subdomain URL |
| **Personal email blocked** | Free trials often reject gmail.com, yahoo.com, icloud.com — use a work email or [contact PagerDuty support](https://www.pagerduty.com/contact-us/) |
| **Wrong / stale subdomain** | Do not bookmark `aspensif-1.pagerduty.com` directly — log in at [identity.pagerduty.com](https://identity.pagerduty.com) or [pagerduty.com](https://www.pagerduty.com) with your email |
| **Trial expired or account deactivated** | Sign up again with a new subdomain, or contact support to reactivate |
| **Partial signup failure** | Try a fresh signup with a different account URL name (5–40 chars, unique) |

**Try this login order:**

1. Go to [https://identity.pagerduty.com](https://identity.pagerduty.com)
2. Enter the **same email** you used at signup
3. Complete any email verification step
4. If prompted, pick the correct account/region from the list

If none of that works, open a ticket with PagerDuty Support and include your signup email and subdomain (`aspensif-1`).

### Continue Week 1 without PagerDuty (dev fallback)

PagerDuty is **optional for local kickoff**. If the account is unavailable, leave `PAGERDUTY_ROUTING_KEY` empty in `observability/.env` — Alertmanager uses `alertmanager.no-pagerduty.yml` and alerts stay visible at [http://localhost:9093](http://localhost:9093).

Verify the alert loop locally:

```bash
curl -X POST http://localhost:9093/api/v2/alerts \
  -H 'Content-Type: application/json' \
  -d '[{
    "labels": {"alertname":"KickoffTest","severity":"critical"},
    "annotations": {"summary":"Local Alertmanager test (no PagerDuty)"},
    "startsAt": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'"
  }]'
```

Open **http://localhost:9093/#/alerts** — you should see `KickoffTest` within seconds.

Add PagerDuty later when the account is working; only the integration key is needed in `.env`.

---

## Next step

→ [05-verify-before-kickoff.md](./05-verify-before-kickoff.md) — final checklist before Day 1
