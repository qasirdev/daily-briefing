"""Security utilities for the briefing backend."""

from backend.security.constitutional import ConstitutionalClassifier, ConstitutionalResult
from backend.security.injection import InjectionDetectionResult, PromptInjectionDetector
from backend.security.pii import PIIDetector, mask_pii
from backend.security.prompt_guard import PromptGuardScanResult, PromptGuardService
from backend.security.sanitization import sanitize_markdown
from backend.security.spotlighting import (
    EXTERNAL_CONTENT_CLOSE,
    EXTERNAL_CONTENT_OPEN,
    extract_spotlighted_content,
    is_spotlighted,
    spotlight_external_content,
)

__all__ = [
    "ConstitutionalClassifier",
    "ConstitutionalResult",
    "EXTERNAL_CONTENT_CLOSE",
    "EXTERNAL_CONTENT_OPEN",
    "InjectionDetectionResult",
    "PIIDetector",
    "PromptGuardScanResult",
    "PromptGuardService",
    "PromptInjectionDetector",
    "extract_spotlighted_content",
    "is_spotlighted",
    "mask_pii",
    "sanitize_markdown",
    "spotlight_external_content",
]
