"""Supply chain CI policy constants (DB-122)."""

from backend.security.bom import load_ai_bom, openssf_scorecard_minimum

PIP_AUDIT_BLOCK_SEVERITIES = ("critical", "high")
PIP_AUDIT_IGNORED_VULNS = ("GHSA-rrmf-rvhw-rf47",)


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


def test_pip_audit_ignored_vulns_documented_in_ai_bom() -> None:
    bom = load_ai_bom()
    ignored = bom["metadata"]["supply_chain"]["pip_audit_ignored_vulns"]
    ids = tuple(entry["id"] for entry in ignored)
    assert ids == PIP_AUDIT_IGNORED_VULNS
    for entry in ignored:
        assert entry.get("expires")
        assert entry.get("reason")
