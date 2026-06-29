"""Tests for prompt version registry."""

from __future__ import annotations

from collections.abc import Generator

import pytest

from backend import prompt_version


@pytest.fixture(autouse=True)
def _reset_version_state() -> Generator[None, None, None]:
    prompt_version.clear_version_cache()
    prompt_version.register_version_snapshot()
    yield
    prompt_version.clear_version_cache()


def test_parse_contract_version_reads_contract_md() -> None:
    version = prompt_version.parse_contract_version("verification")
    assert version == "v2.0.0"


def test_parse_contract_version_reads_critic_v2() -> None:
    version = prompt_version.parse_contract_version("critic")
    assert version == "v2.0.0"


def test_parse_contract_version_defaults_when_missing() -> None:
    version = prompt_version.parse_contract_version("nonexistent_agent_xyz")
    assert version == "v1.5.0"


def test_resolve_prompt_version_is_cached() -> None:
    first = prompt_version.resolve_prompt_version("focus")
    second = prompt_version.resolve_prompt_version("focus")
    assert first == second
    assert first == "v2.0.0"


def test_detect_version_changes_after_snapshot_update(monkeypatch: pytest.MonkeyPatch) -> None:
    prompt_version._version_snapshot["test_agent"] = "v1.0.0"
    monkeypatch.setattr(
        prompt_version,
        "list_agent_prompt_versions",
        lambda: {"test_agent": "v2.0.0"},
    )
    changes = prompt_version.detect_version_changes()
    assert changes == [("test_agent", "v1.0.0", "v2.0.0")]


def test_list_agent_prompt_versions_includes_known_agents() -> None:
    versions = prompt_version.list_agent_prompt_versions()
    assert "focus" in versions
    assert "verification" in versions
    assert "critic" in versions
    assert versions["critic"] == "v2.0.0"
    assert prompt_version.VERSION_PATTERN.match(versions["focus"])
