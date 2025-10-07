"""Contract test ensuring --target-file writes Markdown with request/response details."""

from __future__ import annotations

from collections.abc import Callable
import json
from pathlib import Path
from typing import Any

from click.testing import CliRunner
import pytest

from zte_daemon.cli.main import cli


class StubClient:
    def __init__(self, *, on_request: Callable[[str, str, Any | None], dict[str, Any]]) -> None:
        self._on_request = on_request

    def __enter__(self) -> "StubClient":
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:  # pragma: no cover - trivial
        return False

    def login(self, password: str) -> bool:
        return True

    def request(
        self,
        path: str,
        *,
        method: str,
        payload: Any | None,
        expects: str,
    ) -> dict[str, Any]:
        return self._on_request(path, method, payload)


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


def test_target_file_writes_markdown(tmp_path: Path, runner: CliRunner, monkeypatch: pytest.MonkeyPatch) -> None:
    def capture(path: str, method: str, payload: Any | None) -> dict[str, Any]:
        assert method == "POST"
        assert payload == {"foo": "bar"}
        return {"status": "ok", "data": [1, 2, 3]}

    import importlib

    discover_mod = importlib.import_module("zte_daemon.cli.commands.discover")
    monkeypatch.setattr(
        discover_mod,
        "ZTEClient",
        lambda host, **_: StubClient(on_request=capture),
    )

    target_file = tmp_path / "docs" / "discover" / "lan_station_list.md"

    result = runner.invoke(
        cli,
        [
            "discover",
            "--host",
            "192.168.0.1",
            "--password",
            "secret",
            "--path",
            "goform/example",
            "--payload",
            '{"foo": "bar"}',
            "--target-file",
            str(target_file),
        ],
        catch_exceptions=False,
    )

    assert result.exit_code == 0
    assert target_file.exists()
    content = target_file.read_text()
    assert "## Request" in content
    assert "Method: POST" in content
    assert '"foo": "bar"' in content
    assert '"status": "ok"' in content
    assert "## Response" in content
    assert str(target_file) in result.output
    snapshot_file = target_file.with_suffix(".json")
    assert snapshot_file.exists()
    payload = json.loads(snapshot_file.read_text())
    assert payload["metadata"]["method"] == "POST"
    assert payload["metadata"]["path"] == "goform/example"
    assert payload["data"]["status"] == "ok"
