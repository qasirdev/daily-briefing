# Local LLM Fallback

**Version:** 1.1.0 | **Last Updated:** May 2026

---

## Overview

The briefing assistant routes LLM requests based on data classification and provider health:

| Trigger | Behaviour |
|---|---|
| Input is **`confidential_pii`** (Focus agent with tasks/calendar) | Local LLM **if enabled**; else **masked OpenRouter** |
| Local LLM **unreachable** (e.g. wrong URL in Docker) | **Masked OpenRouter** fallback when `OPENROUTER_API_KEY` is set |
| OpenRouter **429** / **timeout** | Local LLM fallback when `LOCAL_LLM_ENABLED=true` |

---

## Configuration

```bash
LOCAL_LLM_ENABLED=false          # recommended for Docker + OpenRouter-only dev
LOCAL_LLM_BASE_URL=http://localhost:8080/v1
LOCAL_LLM_MODEL_ID=local/llama-3-8b
```

| Variable | Description |
|---|---|
| `LOCAL_LLM_ENABLED` | Enable local OpenAI-compatible client |
| `LOCAL_LLM_BASE_URL` | Base URL (must be reachable from where FastAPI runs) |
| `LOCAL_LLM_MODEL_ID` | Model id sent in API requests |

### Docker vs local dev

| Environment | `LOCAL_LLM_BASE_URL` |
|---|---|
| **Local uvicorn** (host) | `http://localhost:8080/v1` |
| **Docker container** | `http://host.docker.internal:8080/v1` (Mac/Windows Docker Desktop) |

Do **not** use `http://localhost:8080` inside Docker — that is the container itself, not your Mac. `docker-compose.yml` includes `host.docker.internal:host-gateway`.

When `LOCAL_LLM_ENABLED=false`, Focus agent PII data is sent to OpenRouter with `mask_pii()` applied — no local server required.

---

## Supported setups

| Server | Notes |
|---|---|
| [llama.cpp server](https://github.com/ggerganov/llama.cpp) | `--port 8080`, OpenAI API compatible |
| vLLM | `--api-key local` with OpenAI client |
| Ollama | OpenAI compatibility layer on port 11434/v1 |

---

## Metrics

Fallback events increment `llm_fallback_total` with labels:

- `from_model` — primary OpenRouter model
- `to_model` — local model id
- `reason` — `pii`, `timeout`, `rate_limit`, or `provider_error`

---

## Testing locally

```bash
# Terminal 1 — local model (example)
llama-server --model ./models/llama-3-8b.gguf --port 8080

# Terminal 2 — backend (local dev port 8010)
LOCAL_LLM_ENABLED=true uv run uvicorn backend.main:app --reload \
  --reload-dir backend --reload-dir prompts \
  --host 127.0.0.1 --port 8010
```

Generate a briefing with task/calendar data to trigger PII routing.

---

*Local LLM — Version 1.1.0 — May 2026*
