"""OWASP GenAI Top 10 boundary test matrix (testing.mdc)."""

from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]

OWASP_GENAI_MATRIX: list[tuple[str, str, str, str]] = [
    ("LLM01", "Prompt Injection", "backend/tests/security/test_injection.py", "required"),
    (
        "LLM02",
        "Insecure Output Handling",
        "backend/tests/security/test_sanitization.py",
        "required",
    ),
    ("LLM03", "Training Data Poisoning", "", "not_applicable"),
    ("LLM04", "Model Denial of Service", "backend/tests/security/test_rate_limits.py", "required"),
    (
        "LLM05",
        "Supply Chain Vulnerabilities",
        "backend/tests/security/test_dependencies.py",
        "required",
    ),
    (
        "LLM06",
        "Sensitive Information Disclosure",
        "backend/tests/security/test_pii_masking.py",
        "required",
    ),
    ("LLM07", "Insecure Plugin Design", "backend/tests/security/test_mcp_security.py", "required"),
    ("LLM08", "Excessive Agency", "backend/tests/security/test_agent_scope.py", "required"),
    ("LLM09", "Overreliance", "", "not_applicable"),
    ("LLM10", "Model Theft", "", "not_applicable"),
]


@pytest.mark.parametrize(
    ("owasp_id", "vulnerability", "test_module", "status"),
    OWASP_GENAI_MATRIX,
    ids=[row[0] for row in OWASP_GENAI_MATRIX],
)
def test_owasp_genai_matrix_coverage(
    owasp_id: str,
    vulnerability: str,
    test_module: str,
    status: str,
) -> None:
    """Every required OWASP GenAI control must have a dedicated test module."""
    assert owasp_id
    assert vulnerability
    if status == "not_applicable":
        pytest.skip(f"{owasp_id} not applicable")
    test_path = REPO_ROOT / test_module
    assert test_path.is_file(), f"{owasp_id} missing test file: {test_module}"


def test_all_ten_owasp_genai_ids_present() -> None:
    ids = {row[0] for row in OWASP_GENAI_MATRIX}
    assert ids == {f"LLM0{i}" for i in range(1, 10)} | {"LLM10"}
