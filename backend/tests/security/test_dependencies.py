"""Supply chain dependency pinning tests."""

from pathlib import Path


def test_uv_lock_exists() -> None:
    lockfile = Path("uv.lock")
    assert lockfile.is_file()
    assert lockfile.stat().st_size > 0


def test_pyproject_pins_python() -> None:
    text = Path("pyproject.toml").read_text(encoding="utf-8")
    assert "requires-python" in text
