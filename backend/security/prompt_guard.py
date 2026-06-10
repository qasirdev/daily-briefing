"""Meta LlamaFirewall PromptGuard 2 integration (lazy-loaded ML classifier)."""

from __future__ import annotations

import threading
from typing import TYPE_CHECKING, Protocol, cast

import structlog
from pydantic import BaseModel, ConfigDict, Field

from backend.logging_config import get_security_logger

if TYPE_CHECKING:
    pass

LOG = structlog.get_logger(__name__)

_load_lock = threading.Lock()
_guard_instance: PromptGuardBackend | None = None
_load_failed = False


class PromptGuardScanResult(BaseModel):
    """Outcome of PromptGuard 2 ML classification."""

    model_config = ConfigDict(strict=True, frozen=True)

    is_blocked: bool
    score: float = Field(default=0.0, ge=0.0, le=1.0)
    skipped: bool = False
    reason: str | None = None


class PromptGuardBackend(Protocol):
    """Protocol for PromptGuard backends (live model or test double)."""

    def get_jailbreak_score(self, text: str) -> float:
        """Return jailbreak probability in [0.0, 1.0]."""


class PromptGuardService:
    """Lazy-loaded PromptGuard 2 classifier with graceful fallback when unavailable."""

    def __init__(
        self,
        *,
        enabled: bool = True,
        block_threshold: float = 0.9,
        model_name: str = "meta-llama/Llama-Prompt-Guard-2-86M",
        backend: PromptGuardBackend | None = None,
    ) -> None:
        self._enabled = enabled
        self._block_threshold = block_threshold
        self._model_name = model_name
        self._backend = backend

    def scan(
        self,
        text: str,
        *,
        trace_id: str,
        source: str = "unknown",
    ) -> PromptGuardScanResult:
        if not self._enabled or not text.strip():
            return PromptGuardScanResult(is_blocked=False, skipped=True)

        backend = self._backend if self._backend is not None else _load_guard(self._model_name)
        if backend is None:
            return PromptGuardScanResult(is_blocked=False, skipped=True)

        score = backend.get_jailbreak_score(text)
        if score >= self._block_threshold:
            logger = get_security_logger()
            logger.warning(
                "prompt_guard_blocked",
                trace_id=trace_id,
                source=source,
                score=score,
                threshold=self._block_threshold,
                model=self._model_name,
            )
            return PromptGuardScanResult(
                is_blocked=True,
                score=score,
                reason="prompt_guard_jailbreak_detected",
            )
        return PromptGuardScanResult(is_blocked=False, score=score)


def _load_guard(model_name: str) -> PromptGuardBackend | None:
    global _guard_instance, _load_failed

    if _load_failed:
        return None
    if _guard_instance is not None:
        return _guard_instance

    with _load_lock:
        if _load_failed:
            return None
        if _guard_instance is not None:
            return _guard_instance
        try:
            from llamafirewall.scanners.promptguard_utils import PromptGuard

            LOG.info("loading_prompt_guard_model", model=model_name)
            _guard_instance = cast(PromptGuardBackend, PromptGuard())
            return _guard_instance
        except Exception as exc:
            _load_failed = True
            LOG.warning(
                "prompt_guard_unavailable",
                model=model_name,
                error=str(exc),
                hint="Set HF_TOKEN and preload meta-llama/Llama-Prompt-Guard-2-86M, "
                "or disable via LLAMAFIREWALL_ENABLED=false",
            )
            return None


def reset_prompt_guard_cache() -> None:
    """Reset lazy loader state (for tests)."""
    global _guard_instance, _load_failed
    with _load_lock:
        _guard_instance = None
        _load_failed = False


def build_prompt_guard_service() -> PromptGuardService:
    """Construct a PromptGuardService from application settings."""
    from backend.settings import get_settings

    settings = get_settings()
    return PromptGuardService(
        enabled=settings.llamafirewall_enabled,
        block_threshold=settings.llamafirewall_block_threshold,
        model_name=settings.llamafirewall_model,
    )
