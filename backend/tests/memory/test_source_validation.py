"""Tests for semantic source validation."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from backend.memory.semantic import SemanticMemoryRecord
from backend.memory.source_validation import cross_reference_records, validate_source_provenance

NOW = datetime.now(UTC)


def _record(
    *,
    content: str,
    source_id: str | None = None,
    source_trust: str = "internal",
    similarity: float = 0.9,
) -> SemanticMemoryRecord:
    return SemanticMemoryRecord(
        id=uuid.uuid4(),
        user_id="user-1",
        content=content,
        source_type="briefing",
        source_id=source_id,
        source_trust=source_trust,
        similarity=similarity,
        created_at=NOW,
    )


def test_untrusted_source_excluded() -> None:
    records = [_record(content="poison", source_trust="untrusted")]
    assert cross_reference_records(records) == []


def test_duplicate_content_keeps_higher_similarity() -> None:
    records = [
        _record(content="Same lesson", source_id="a", similarity=0.7),
        _record(content="Same lesson", source_id="b", similarity=0.95),
    ]
    filtered = cross_reference_records(records)
    assert len(filtered) == 1
    assert filtered[0].similarity == 0.95


def test_conflicting_source_ids_dropped() -> None:
    records = [
        _record(content="Lesson A", source_id="src-1", similarity=0.9),
        _record(content="lesson a", source_id="src-2", similarity=0.95),
    ]
    filtered = cross_reference_records(records)
    assert len(filtered) == 1


def test_validate_source_provenance_drop_count() -> None:
    records = [
        _record(content="ok", source_trust="internal"),
        _record(content="bad", source_trust="untrusted"),
    ]
    validated, dropped = validate_source_provenance(records)
    assert len(validated) == 1
    assert dropped == 1


def test_empty_records_no_op() -> None:
    validated, dropped = validate_source_provenance([])
    assert validated == []
    assert dropped == 0
