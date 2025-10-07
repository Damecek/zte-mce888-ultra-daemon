"""Integration tests for the `zte discover` command."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from click.testing import CliRunner
import httpx
import pytest

from zte_daemon.cli.main import cli
from zte_daemon.modem.zte_client import AuthenticationError, RequestError


class ScenarioClient:
    def __init__(self, *, scenario: str, on_request: Callable[[str, str, Any | None], None] | None = None) -> None:
        self._scenario = scenario
        self._on_request = on_request

    def __enter__(self) -> "ScenarioClient":
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:  # pragma: no cover - trivial
        return False

    def login(self, password: str) -> bool:
        if self._scenario == "auth-failure":
            raise AuthenticationError("invalid credentials")
        return True

    def request(
        self,
        path: str,
        *,
        method: str,
        payload: Any | None,
        expects: str,
    ) -> Any:
        if self._scenario == "network":
            raise RequestError("network unreachable") from httpx.ConnectError(
                "boom", request=httpx.Request(method, httpx.URL("http://modem"))
            )
        if self._on_request:
            self._on_request(path, method, payload)
        return {"status": "ok", "path": path}


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


def test_discover_reports_network_error(runner: CliRunner, monkeypatch: pytest.MonkeyPatch) -> None:
    import importlib

    discover_mod = importlib.import_module("zte_daemon.cli.commands.discover")
    monkeypatch.setattr(
        discover_mod,
        "ZTEClient",
        lambda host, **_: ScenarioClient(scenario="network"),
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

    assert result.exit_code != 0
    assert "Unable to reach modem" in result.output


def test_discover_reports_auth_failure(runner: CliRunner, monkeypatch: pytest.MonkeyPatch) -> None:
    import importlib

    discover_mod = importlib.import_module("zte_daemon.cli.commands.discover")
    monkeypatch.setattr(
        discover_mod,
        "ZTEClient",
        lambda host, **_: ScenarioClient(scenario="auth-failure"),
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

    assert result.exit_code != 0
    assert "Authentication failed" in result.output


def test_discover_successful_flow_outputs_json(runner: CliRunner, monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, Any] = {}

    def capture(path: str, method: str, payload: Any | None) -> None:
        captured.update({"path": path, "method": method, "payload": payload})

    import importlib

    discover_mod = importlib.import_module("zte_daemon.cli.commands.discover")
    monkeypatch.setattr(
        discover_mod,
        "ZTEClient",
        lambda host, **_: ScenarioClient(scenario="success", on_request=capture),
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
    assert captured == {"path": "goform/example", "method": "GET", "payload": None}
    assert '"status": "ok"' in result.output
