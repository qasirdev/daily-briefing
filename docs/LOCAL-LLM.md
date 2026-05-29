# Local LLM Fallback — AI Daily Briefing Assistant

**Version:** 1.5.0 | **Last Updated:** May 2026

---

## Overview

The AI Daily Briefing Assistant supports local LLM inference as a privacy-first fallback when:
- OpenRouter API is unavailable or rate-limited
- Data contains sensitive PII that shouldn't leave the device
- User explicitly prefers local processing
- Cost optimization is required

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     LLM Router                               │
│  ┌─────────────────────────────────────────────────────┐    │
│  │                 Model Selection                      │    │
│  │                                                      │    │
│  │  ┌─────────────┐    ┌─────────────┐                 │    │
│  │  │  Primary    │    │  Fallback   │                 │    │
│  │  │  OpenRouter │───▶│  Local LLM  │                 │    │
│  │  │             │    │             │                 │    │
│  │  └─────────────┘    └─────────────┘                 │    │
│  │        │                   │                         │    │
│  │        ▼                   ▼                         │    │
│  │  Rate limit?         PII detected?                   │    │
│  │  API error?          Privacy flag?                   │    │
│  │  Timeout?            User preference?                │    │
│  │                                                      │    │
│  └─────────────────────────────────────────────────────┘    │
│                          │                                   │
│                          ▼                                   │
│  ┌─────────────────────────────────────────────────────┐    │
│  │              OpenAI-Compatible SDK                   │    │
│  │         (same interface for both providers)          │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

---

## Configuration

### Environment Variables

```bash
# .env

# Enable local LLM fallback
LOCAL_LLM_ENABLED=true

# Local LLM server endpoint (OpenAI-compatible)
LOCAL_LLM_BASE_URL=http://localhost:8080/v1

# Model identifier (for logging/metrics)
LOCAL_LLM_MODEL_ID=llama-3-8b-instruct

# Fallback triggers
LLM_FALLBACK_ON_RATE_LIMIT=true
LLM_FALLBACK_ON_TIMEOUT=true
LLM_FALLBACK_ON_PII=true

# Timeouts (seconds)
LOCAL_LLM_TIMEOUT=60
OPENROUTER_TIMEOUT=30
```

### Settings Validation

```python
from pydantic_settings import BaseSettings

class LLMSettings(BaseSettings):
    # Primary (OpenRouter)
    openrouter_api_key: str
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_timeout: int = 30
    llm_primary_model: str = "openai/gpt-4o-mini"
    
    # Fallback (Local)
    local_llm_enabled: bool = False
    local_llm_base_url: str = "http://localhost:8080/v1"
    local_llm_model_id: str = "llama-3-8b-instruct"
    local_llm_timeout: int = 60
    
    # Fallback triggers
    llm_fallback_on_rate_limit: bool = True
    llm_fallback_on_timeout: bool = True
    llm_fallback_on_pii: bool = True
```

---

## Supported Local LLM Servers

### Primary: llama.cpp Server

Recommended for production use with GGUF quantized models.

```bash
# Install llama.cpp
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp && make -j

# Download quantized model
wget https://huggingface.co/TheBloke/Llama-3-8B-Instruct-GGUF/resolve/main/llama-3-8b-instruct.Q4_K_M.gguf

# Start server
./llama-server \
  --model llama-3-8b-instruct.Q4_K_M.gguf \
  --host 0.0.0.0 \
  --port 8080 \
  --ctx-size 4096 \
  --n-gpu-layers 35  # Adjust based on VRAM
```

### Alternative: LiteLLM Proxy

For unified interface across multiple local models.

```bash
# Install LiteLLM
pip install litellm[proxy]

# Start proxy
litellm --model ollama/llama3:8b --port 8080
```

### Alternative: Ollama

Easy setup for development environments.

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Pull model
ollama pull llama3:8b-instruct-q4_K_M

# Serve with OpenAI compatibility
OLLAMA_HOST=0.0.0.0 ollama serve
```

---

## Recommended Models

> [!NOTE]
> The models listed below are considered **minimum viable** for the architecture. Given the rapid pace of open-source LLM releases (e.g., Llama 4, Mistral Nemo), always check for the latest quantized releases that fit your hardware constraints.

### For Daily Briefing Generation (Minimum Viable)

| Model | Quantization | VRAM | Quality | Speed | Recommended |
|---|---|---|---|---|---|
| Llama 3 8B Instruct | Q4_K_M | 6 GB | Good | Fast | ✅ Default |
| Llama 3 8B Instruct | Q5_K_M | 7 GB | Better | Medium | Development |
| Llama 3 8B Instruct | Q8_0 | 10 GB | Best | Slower | Quality-first |
| Mistral 7B Instruct | Q4_K_M | 5 GB | Good | Fast | Low VRAM |
| Phi-3 Mini | Q4_K_M | 3 GB | Acceptable | Very Fast | CPU-only |

### Model Selection Guide

```python
def select_local_model(
    available_vram_gb: float,
    quality_priority: bool = False,
) -> str:
    """Select appropriate local model based on hardware."""
    
    if available_vram_gb >= 10 and quality_priority:
        return "llama-3-8b-instruct.Q8_0.gguf"
    elif available_vram_gb >= 6:
        return "llama-3-8b-instruct.Q4_K_M.gguf"
    elif available_vram_gb >= 4:
        return "mistral-7b-instruct-v0.3.Q4_K_M.gguf"
    else:
        return "phi-3-mini-4k-instruct.Q4_K_M.gguf"
```

---

## Hardware Requirements

### Minimum Requirements

| Component | Requirement | Notes |
|---|---|---|
| **CPU** | 8+ cores | AVX2 support required |
| **RAM** | 16 GB | For model loading + context |
| **Storage** | 10 GB free | For model files |
| **GPU** | Optional | Significantly improves speed |

### Recommended Requirements

| Component | Requirement | Notes |
|---|---|---|
| **CPU** | 12+ cores | Modern Intel/AMD or Apple Silicon |
| **RAM** | 32 GB | Comfortable headroom |
| **Storage** | SSD, 50 GB free | Fast model loading |
| **GPU** | 8+ GB VRAM | NVIDIA RTX 3070+ or Apple M1+ |

### Platform-Specific Notes

#### Apple Silicon (M1/M2/M3)

```bash
# llama.cpp uses Metal for GPU acceleration automatically
./llama-server \
  --model llama-3-8b-instruct.Q4_K_M.gguf \
  --n-gpu-layers 99  # All layers on GPU
```

#### NVIDIA GPU

```bash
# Ensure CUDA support is compiled
./llama-server \
  --model llama-3-8b-instruct.Q4_K_M.gguf \
  --n-gpu-layers 35  # Adjust based on VRAM
```

#### CPU-Only

```bash
# Use smaller model or lower quantization
./llama-server \
  --model phi-3-mini-4k-instruct.Q4_K_M.gguf \
  --threads 8  # Match physical cores
```

---

## LLM Router Implementation

```python
from dataclasses import dataclass
from typing import Literal
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

@dataclass
class LLMResponse:
    content: str
    model_used: str
    tokens_input: int
    tokens_output: int
    latency_ms: int
    fallback_used: bool

class LLMRouter:
    """Routes LLM requests with automatic fallback."""
    
    def __init__(self, settings: LLMSettings):
        self.settings = settings
        self.primary_client = httpx.AsyncClient(
            base_url=settings.openrouter_base_url,
            headers={"Authorization": f"Bearer {settings.openrouter_api_key}"},
            timeout=settings.openrouter_timeout,
        )
        
        if settings.local_llm_enabled:
            self.fallback_client = httpx.AsyncClient(
                base_url=settings.local_llm_base_url,
                timeout=settings.local_llm_timeout,
            )
        else:
            self.fallback_client = None
    
    async def generate(
        self,
        messages: list[dict],
        agent_id: str,
        trace_id: str,
        force_local: bool = False,
        data_classification: str = "internal",
    ) -> LLMResponse:
        """Generate completion with automatic fallback."""
        
        # Check if local should be forced
        use_local = force_local or (
            data_classification == "confidential_pii" 
            and self.settings.llm_fallback_on_pii
        )
        
        if use_local and self.fallback_client:
            return await self._call_local(messages, agent_id, trace_id)
        
        try:
            return await self._call_primary(messages, agent_id, trace_id)
        except (RateLimitError, TimeoutError, APIError) as e:
            if self.fallback_client and self._should_fallback(e):
                logger.warning(
                    "llm_fallback_triggered",
                    agent_id=agent_id,
                    trace_id=trace_id,
                    reason=type(e).__name__,
                )
                return await self._call_local(messages, agent_id, trace_id)
            raise
    
    def _should_fallback(self, error: Exception) -> bool:
        if isinstance(error, RateLimitError):
            return self.settings.llm_fallback_on_rate_limit
        if isinstance(error, TimeoutError):
            return self.settings.llm_fallback_on_timeout
        return False
    
    @retry(stop=stop_after_attempt(2), wait=wait_exponential(min=1, max=10))
    async def _call_primary(
        self,
        messages: list[dict],
        agent_id: str,
        trace_id: str,
    ) -> LLMResponse:
        """Call OpenRouter API."""
        start = time.perf_counter()
        
        response = await self.primary_client.post(
            "/chat/completions",
            json={
                "model": self.settings.llm_primary_model,
                "messages": messages,
            },
        )
        response.raise_for_status()
        
        data = response.json()
        latency_ms = int((time.perf_counter() - start) * 1000)
        
        return LLMResponse(
            content=data["choices"][0]["message"]["content"],
            model_used=self.settings.llm_primary_model,
            tokens_input=data["usage"]["prompt_tokens"],
            tokens_output=data["usage"]["completion_tokens"],
            latency_ms=latency_ms,
            fallback_used=False,
        )
    
    async def _call_local(
        self,
        messages: list[dict],
        agent_id: str,
        trace_id: str,
    ) -> LLMResponse:
        """Call local LLM server."""
        start = time.perf_counter()
        
        response = await self.fallback_client.post(
            "/chat/completions",
            json={
                "model": self.settings.local_llm_model_id,
                "messages": messages,
            },
        )
        response.raise_for_status()
        
        data = response.json()
        latency_ms = int((time.perf_counter() - start) * 1000)
        
        return LLMResponse(
            content=data["choices"][0]["message"]["content"],
            model_used=f"local/{self.settings.local_llm_model_id}",
            tokens_input=data["usage"]["prompt_tokens"],
            tokens_output=data["usage"]["completion_tokens"],
            latency_ms=latency_ms,
            fallback_used=True,
        )
```

---

## Performance Benchmarks

### Briefing Generation Latency

| Model | Hardware | Tokens/sec | P50 Latency | P95 Latency |
|---|---|---|---|---|
| GPT-4o-mini (OpenRouter) | Cloud | 100+ | 1.5s | 3.0s |
| Llama 3 8B Q4_K_M | RTX 4090 | 80 | 2.0s | 4.0s |
| Llama 3 8B Q4_K_M | M2 Pro | 45 | 3.5s | 6.0s |
| Llama 3 8B Q4_K_M | CPU (12-core) | 15 | 10.0s | 15.0s |

### Quality Comparison

| Metric | GPT-4o-mini | Llama 3 8B | Mistral 7B |
|---|---|---|---|
| Instruction Following | Excellent | Good | Good |
| Formatting Consistency | Excellent | Good | Acceptable |
| Task Prioritization | Excellent | Good | Acceptable |
| Overall Quality | 95% | 85% | 75% |

---

## Monitoring

### Local LLM Metrics

| Metric | Type | Description |
|---|---|---|
| `local_llm_requests_total` | Counter | Total local LLM requests |
| `local_llm_latency_seconds` | Histogram | Request latency |
| `local_llm_tokens_per_second` | Gauge | Current throughput |
| `llm_fallback_total` | Counter | Fallback triggers by reason |

### Health Check

```python
async def check_local_llm_health() -> dict:
    """Check local LLM server health."""
    try:
        response = await fallback_client.get("/health")
        return {
            "status": "healthy",
            "latency_ms": response.elapsed.total_seconds() * 1000,
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
        }
```

---

## Troubleshooting

### Common Issues

| Issue | Cause | Solution |
|---|---|---|
| Slow inference | CPU-only or insufficient VRAM | Use smaller model or GPU |
| Out of memory | Model too large | Use Q4 quantization |
| Context overflow | Input too long | Reduce context or use sliding window |
| Poor quality | Model too small | Use Llama 3 8B or larger |

### Debug Logging

```bash
# Enable verbose logging for llama.cpp
./llama-server \
  --model model.gguf \
  --log-enable \
  --log-file llama-server.log
```

---

*Local LLM Documentation — Version 1.5.0 — May 2026*
