from __future__ import annotations

from pathlib import Path


def test_readme_mentions_quickstart_commands() -> None:
    readme = Path("README.md").read_text()
    assert "uv run pytest" in readme
    assert "tests/fixtures/modem" in readme
