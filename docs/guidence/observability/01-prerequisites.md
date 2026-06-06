# Step 1 — Prerequisites

Complete these before installing Prometheus, Grafana, or PagerDuty.

---

## Required software

| Tool | Version | Check command |
|------|---------|---------------|
| Docker Desktop | Latest | `docker --version` |
| Node.js | 22+ | `nvm use 22 && node --version` |
| Python | 3.12+ | `uv run python --version` |
| uv | Latest | `uv --version` |

Install Docker Desktop from [docker.com](https://www.docker.com/products/docker-desktop/).

---

## Clone and sync the project

```bash
cd daily-briefing
git checkout epic/autonomus-implementation-gap
uv sync
```

---

## Accounts to create (free tiers)

Create these accounts **before** the setup steps — you will need credentials during configuration.

| Service | Sign up | What you need from it |
|---------|---------|------------------------|
| Grafana Cloud (optional) | [Free account](https://grafana.com/auth/sign-up/create-user?pg=pricing&plcmt=free&cta=create-free-account) | Stack URL, API token (Path B only) |
| PagerDuty | [Start for Free](https://www.pagerduty.com/) | Events API v2 Integration Key |
| Prometheus | No account | Self-hosted via Docker |

> **Tip:** For Week 1 kickoff, use **local Grafana in Docker** (included in our compose file) instead of Grafana Cloud — fewer steps.

---

## Start the backend (keep running during setup)

Prometheus needs something to scrape. In a dedicated terminal:

```bash
nvm use 22
cd daily-briefing
uv run uvicorn backend.main:app --host 0.0.0.0 --port 8010 --reload
```

Verify:

```bash
curl http://localhost:8010/health
curl http://localhost:8010/metrics | head -5
```

---

## Next step

→ [02-prometheus-setup.md](./02-prometheus-setup.md)
