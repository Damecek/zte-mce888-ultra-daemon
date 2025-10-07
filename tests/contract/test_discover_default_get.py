"""CLI contract test: discover defaults to GET when no payload is provided."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from click.testing import CliRunner
import pytest

from zte_daemon.cli.main import cli


class StubClient:
    def __init__(self, *, on_request: Callable[[str, str, Any | None], None]) -> None:
        self._on_request = on_request

    def __enter__(self) -> "StubClient":
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:  # pragma: no cover - trivial
        return False

    def login(self, password: str) -> bool:  # pragma: no cover - exercised in contract tests
        assert password == "secret"
        return True

    def request(
        self,
        path: str,
        *,
        method: str,
        payload: Any | None,
        expects: str,
    ) -> dict[str, Any]:
        self._on_request(path, method, payload)
        assert expects == "json"
        return {"result": "ok"}


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


def test_discover_defaults_to_get(runner: CliRunner, monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, Any] = {}

    def capture(path: str, method: str, payload: Any | None) -> None:
        captured.update({"path": path, "method": method, "payload": payload})

    # Delay import to allow ModuleNotFoundError to surface until implementation exists
    import importlib

    discover_mod = importlib.import_module("zte_daemon.cli.commands.discover")
    monkeypatch.setattr(
        discover_mod,
        "ZTEClient",
        lambda host, **_: StubClient(on_request=capture),
    )

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
        ],
        catch_exceptions=False,
    )

    assert result.exit_code == 0
    assert captured["path"] == "goform/example"
    assert captured["method"] == "GET"
    assert captured["payload"] is None
