"""PII detection and masking tests."""

from backend.security.pii import PIIDetector, mask_pii


def test_email_masked() -> None:
    text = "Contact user@example.com for details"
    masked = mask_pii(text)
    assert "user@example.com" not in masked
    assert "[REDACTED_EMAIL]" in masked


def test_phone_masked() -> None:
    text = "Call 555-123-4567 today"
    masked = mask_pii(text)
    assert "555-123-4567" not in masked


def test_ssn_masked() -> None:
    text = "SSN 123-45-6789 on file"
    masked = mask_pii(text)
    assert "123-45-6789" not in masked
    assert "[REDACTED_SSN]" in masked


def test_detector_finds_email() -> None:
    detector = PIIDetector()
    matches = detector.detect("Reach me at a.b@c.co")
    assert any(match.kind == "email" for match in matches)
