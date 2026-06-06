"""RAG ingestion validation — pre-store scanning and content provenance (Gap #120)."""

from __future__ import annotations

import hashlib
import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from backend.security.injection import PromptInjectionDetector

SourceTrust = Literal["internal", "trusted", "untrusted"]

RAG_INGESTION_PATTERNS: tuple[tuple[str, re.Pattern[str], float], ...] = (
    ("system_prompt_leak", re.compile(r"system\s*prompt\s*:", re.IGNORECASE), 0.9),
    ("script_tag", re.compile(r"<\s*script\b", re.IGNORECASE), 0.95),
    ("html_embed", re.compile(r"<\s*/?(iframe|object|embed)\b", re.IGNORECASE), 0.9),
    (
        "credential_assignment",
        re.compile(
            r"(?:api[_-]?key|secret[_-]?key|access[_-]?token|bearer(?:\s+\w+)?)\s*[:=]\s*\S+",
            re.IGNORECASE,
        ),
        0.92,
    ),
    ("openai_key", re.compile(r"sk-[a-zA-Z0-9]{20,}", re.IGNORECASE), 0.98),
)

_detector = PromptInjectionDetector()


class IngestionValidationResult(BaseModel):
    """Outcome of semantic memory content validation."""

    model_config = ConfigDict(strict=True, frozen=True)

    accepted: bool
    content_hash: str = Field(..., min_length=64, max_length=64)
    matched_pattern: str | None = None
    reason: str | None = None


class SemanticIngestionRejected(Exception):
    """Raised when semantic memory content fails ingestion validation."""

    def __init__(
        self,
        *,
        reason: str,
        matched_pattern: str | None = None,
    ) -> None:
        super().__init__(reason)
        self.reason = reason
        self.matched_pattern = matched_pattern


def compute_content_hash(content: str) -> str:
    """Return SHA-256 hex digest of normalized content for provenance tracking."""
    normalized = content.strip()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def validate_semantic_content(
    content: str,
    *,
    trace_id: str = "",
    source: str = "semantic_memory",
) -> IngestionValidationResult:
    """Validate semantic memory content before ingestion or retrieval."""
    content_hash = compute_content_hash(content)
    if not content.strip():
        return IngestionValidationResult(
            accepted=False,
            content_hash=content_hash,
            reason="empty_content",
        )

    injection = _detector.scan(content, trace_id=trace_id, source=source)
    if injection.is_suspicious:
        return IngestionValidationResult(
            accepted=False,
            content_hash=content_hash,
            matched_pattern=injection.matched_pattern,
            reason="prompt_injection",
        )

    normalized = PromptInjectionDetector._normalize(content)
    for name, pattern, _confidence in RAG_INGESTION_PATTERNS:
        if pattern.search(normalized):
            return IngestionValidationResult(
                accepted=False,
                content_hash=content_hash,
                matched_pattern=name,
                reason="rag_poisoning",
            )

    return IngestionValidationResult(accepted=True, content_hash=content_hash)
