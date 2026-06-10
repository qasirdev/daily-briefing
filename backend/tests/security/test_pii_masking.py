"""PII detection and masking tests."""

import pytest

from backend.security.pii import PIIDetector, mask_pii

# (input text, secret substring that must be removed, expected placeholder substring)
_MASK_CASES: tuple[tuple[str, str, str], ...] = (
    ("Contact user@example.com for details", "user@example.com", "[REDACTED_EMAIL]"),
    ("Call 07123456789 today", "07123456789", "[REDACTED_PHONE]"),
    ("NINO AB123456C on file", "AB123456C", "[REDACTED_NINO]"),
    ("NHS number 943 476 5919", "943 476 5919", "[REDACTED_NHS]"),
    ("Postcode is EC1A 1BB for delivery", "EC1A 1BB", "REDACTED"),
    ("Card 4111 1111 1111 1111", "4111 1111 1111 1111", "[REDACTED_CARD]"),
    ("Server at 192.168.1.1 failed", "192.168.1.1", "[REDACTED_IP]"),
    ("Pay to GB29NWBK60161331926819 please", "GB29NWBK60161331926819", "[REDACTED_IBAN]"),
    ("DOB 15/03/1985 recorded", "15/03/1985", "[REDACTED_DOB]"),
    ("born 15 March 1985 on file", "15 March 1985", "[REDACTED_DOB]"),
    ("password: SecretPass123", "SecretPass123", "[REDACTED_PASSWORD]"),
    ("Vehicle reg AB12CDE on file", "AB12CDE", "[REDACTED_VRM]"),
    ("Location 51.5074, -0.1278 noted", "51.5074, -0.1278", "[REDACTED_COORDS]"),
    ("VAT GB123456789 registered", "GB123456789", "[REDACTED_VAT]"),
    ("username: jdoe99", "jdoe99", "[REDACTED_USERNAME]"),
    ("MAC aa:bb:cc:dd:ee:ff seen", "aa:bb:cc:dd:ee:ff", "[REDACTED_MAC]"),
    ("PO Box 1234 for mail", "PO Box 1234", "[REDACTED_POBOX]"),
)


@pytest.mark.parametrize(("text", "secret", "placeholder"), _MASK_CASES)
def test_mask_pii_replaces_sensitive_values(text: str, secret: str, placeholder: str) -> None:
    masked = mask_pii(text)
    assert secret not in masked
    assert placeholder in masked


def test_credit_card_detector_rejects_short_digit_runs() -> None:
    """Digit runs below card length must not be classified as credit cards."""
    detector = PIIDetector()
    matches = detector.detect("Invoice total 123456789012")
    assert not any(match.kind == "credit_card" for match in matches)


def test_detector_finds_email() -> None:
    detector = PIIDetector()
    matches = detector.detect("Reach me at a.b@c.co")
    assert any(match.kind == "email" for match in matches)


def test_detector_finds_uk_phone() -> None:
    detector = PIIDetector()
    matches = detector.detect("Mobile 07911123456")
    assert any(match.kind == "phone" for match in matches)


def test_detector_finds_nino() -> None:
    detector = PIIDetector()
    matches = detector.detect("Employee NI AB123456C verified")
    assert any(match.kind == "nino" for match in matches)


def test_detector_finds_multiple_kinds() -> None:
    detector = PIIDetector()
    text = "Contact jane@example.com or 07123456789, NINO AB123456C"
    kinds = {match.kind for match in detector.detect(text)}
    assert "email" in kinds
    assert "phone" in kinds
    assert "nino" in kinds


def test_contains_pii() -> None:
    detector = PIIDetector()
    assert detector.contains_pii("Email me at user@example.com")
    assert not detector.contains_pii("Plain briefing summary for today")


_CALENDAR_DATE_CASES: tuple[str, ...] = (
    "AI Engineer Interview with QM — 05-06-2026 at 14:30",
    "2026-06-05T14:30:00 – 2026-06-05T15:30:00: Scheduled block",
    "05-06-2026 T14:30:00 – 05-06-2026 T15:30:00: Scheduled block",
)


@pytest.mark.parametrize("text", _CALENDAR_DATE_CASES)
def test_calendar_and_iso_datetimes_are_not_masked_as_dob(text: str) -> None:
    """Event and ISO datetimes must not be mistaken for dates of birth."""
    masked = mask_pii(text)
    assert "[REDACTED_DOB]" not in masked
    detector = PIIDetector()
    assert not any(match.kind == "date_of_birth" for match in detector.detect(text))


def test_bare_calendar_date_is_not_date_of_birth() -> None:
    detector = PIIDetector()
    matches = detector.detect("Meeting on 05-06-2026 at 14:30")
    assert not any(match.kind == "date_of_birth" for match in matches)


_CALENDAR_INTERVIEW_CASES: tuple[str, ...] = (
    "SThree: 1st stage interview with Qasir Mehmood - AI Engineer — 10-06-2026 at 12:00",
    "AI Engineer Interview with Qasir Mehmood — 10-06-2026 at 14:00",
)


@pytest.mark.parametrize("text", _CALENDAR_INTERVIEW_CASES)
def test_interview_in_calendar_title_is_not_uk_nic(text: str) -> None:
    """Common 9-letter words in event titles must not be mistaken for UK NIC numbers."""
    masked = mask_pii(text)
    assert "[REDACTED_UKNIC]" not in masked
    assert "interview" in masked.lower()
    detector = PIIDetector()
    assert not any(match.kind == "uk_national_identity_card" for match in detector.detect(text))
