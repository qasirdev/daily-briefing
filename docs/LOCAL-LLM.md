# Local LLM Fallback

**Version:** 1.0.0 | **Last Updated:** May 2026

---

## Overview

The briefing assistant can route LLM requests to a local OpenAI-compatible server when:

- OpenRouter returns **429** (rate limit)
- The primary provider **times out**
- Input is classified as **`confidential_pii`** (tasks/calendar context in the Focus agent)

---

## Configuration

Set these in `.env`:

```bash
LOCAL_LLM_ENABLED=true
LOCAL_LLM_BASE_URL=http://localhost:8080/v1
LOCAL_LLM_MODEL_ID=local/llama-3-8b
```

| Variable | Description |
|---|---|
| `LOCAL_LLM_ENABLED` | Enable fallback client |
| `LOCAL_LLM_BASE_URL` | OpenAI-compatible base URL (e.g. llama.cpp, vLLM) |
| `LOCAL_LLM_MODEL_ID` | Model id sent in API requests |

When `LOCAL_LLM_ENABLED=false`, fallback is disabled and the router raises `LLMError` if the primary provider fails.

---

## Supported setups

| Server | Notes |
|---|---|
| [llama.cpp server](https://github.com/ggerganov/llama.cpp) | `--port 8080`, OpenAI API compatible |
| vLLM | `--api-key local` with OpenAI client |
| Ollama | Use OpenAI compatibility layer on port 11434/v1 |

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

# Terminal 2 — backend
LOCAL_LLM_ENABLED=true uv run uvicorn backend.main:app --reload --host 127.0.0.1 --port 8010
```

Generate a briefing with task/calendar data to trigger PII routing, or simulate OpenRouter failure by leaving `OPENROUTER_API_KEY` empty with fallback enabled.

---

*Local LLM — Version 1.0.0 — May 2026*
