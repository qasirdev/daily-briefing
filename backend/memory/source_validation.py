"""Semantic source validation and cross-referencing (Gap #34)."""

from __future__ import annotations

import structlog

from backend.memory.semantic import SemanticMemoryRecord

logger = structlog.get_logger()

TRUSTED_SOURCES = frozenset({"internal", "trusted"})


def cross_reference_records(
    records: list[SemanticMemoryRecord],
) -> list[SemanticMemoryRecord]:
    """Filter semantic hits with inconsistent source metadata."""
    if not records:
        return []

    seen_content: dict[str, SemanticMemoryRecord] = {}
    validated: list[SemanticMemoryRecord] = []

    for record in records:
        if record.source_trust not in TRUSTED_SOURCES:
            logger.debug(
                "source_validation_untrusted",
                memory_id=str(record.id),
                source_trust=record.source_trust,
            )
            continue

        content_key = record.content.strip().lower()
        existing = seen_content.get(content_key)
        if existing is not None:
            if record.similarity > existing.similarity:
                seen_content[content_key] = record
                if existing in validated:
                    validated.remove(existing)
                validated.append(record)
            continue

        seen_content[content_key] = record
        validated.append(record)

    return validated


def validate_source_provenance(
    records: list[SemanticMemoryRecord],
) -> tuple[list[SemanticMemoryRecord], int]:
    """Cross-reference and deduplicate semantic records; return filtered list and drop count."""
    original_count = len(records)
    filtered = cross_reference_records(records)
    return filtered, original_count - len(filtered)
