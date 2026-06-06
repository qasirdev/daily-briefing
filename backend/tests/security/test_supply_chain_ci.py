"""Supply chain CI policy constants (DB-122)."""

from backend.security.bom import load_ai_bom, openssf_scorecard_minimum

PIP_AUDIT_BLOCK_SEVERITIES = ("critical", "high")


def test_openssf_scorecard_minimum_is_at_least_seven() -> None:
    bom = load_ai_bom()
    assert openssf_scorecard_minimum(bom) >= 7.0


def test_ai_bom_declares_supply_chain_metadata() -> None:
    bom = load_ai_bom()
    metadata = bom["metadata"]
    supply_chain = metadata["supply_chain"]
    assert supply_chain["openssf_scorecard_minimum"] == 7.0
    assert "critical" in supply_chain["pip_audit_block_severity"]
    assert "high" in supply_chain["pip_audit_block_severity"]


def test_pip_audit_block_severities_match_policy() -> None:
    bom = load_ai_bom()
    configured = tuple(bom["metadata"]["supply_chain"]["pip_audit_block_severity"])
    assert configured == PIP_AUDIT_BLOCK_SEVERITIES
