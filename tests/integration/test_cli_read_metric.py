"""Integration tests for `zte read` command."""

from __future__ import annotations

from typing import Any

from click.testing import CliRunner
import httpx
import pytest

from zte_daemon.cli.main import cli
from zte_daemon.modem.zte_client import RequestError


class SnapshotStub:
    def __init__(self, metrics: dict[str, Any]) -> None:
        self._metrics = metrics

    def metric_map(self) -> dict[str, Any]:
        return self._metrics


class StubClient:
    def __init__(self, snapshot: SnapshotStub) -> None:
        self._snapshot = snapshot

    def __enter__(self) -> "StubClient":
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        return False

    def login(self, password: str) -> bool:
        return True

    def fetch_snapshot(self) -> SnapshotStub:
        return self._snapshot


class NetworkErrorClient:
    def __enter__(self) -> "NetworkErrorClient":
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        return False

    def login(self, password: str) -> bool:
        return True

    def fetch_snapshot(self) -> SnapshotStub:
        raise RequestError("network unreachable") from httpx.ConnectError(
            "boom",
            request=httpx.Request("GET", httpx.URL("http://modem")),
        )


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


def test_read_outputs_metric_value(runner: CliRunner, monkeypatch: pytest.MonkeyPatch) -> None:
    import importlib

    read_mod = importlib.import_module("zte_daemon.cli.commands.read")
    monkeypatch.setattr(
        read_mod,
        "ZTEClient",
        lambda host, **_: StubClient(SnapshotStub({"rsrp1": -85, "provider": "TestNet"})),
    )

    result = runner.invoke(
        cli,
        [
            "read",
            "RSRP1",
            "--host",
            "192.168.0.1",
            "--password",
            "secret",
        ],
        catch_exceptions=False,
    )

    assert result.exit_code == 0
    assert "RSRP1: -85" in result.output


def test_read_unknown_metric_produces_error(runner: CliRunner, monkeypatch: pytest.MonkeyPatch) -> None:
    import importlib

    read_mod = importlib.import_module("zte_daemon.cli.commands.read")
    monkeypatch.setattr(
        read_mod,
        "ZTEClient",
        lambda host, **_: StubClient(SnapshotStub({"rsrp1": -85})),
    )

    result = runner.invoke(
        cli,
        [
            "read",
            "invalid",
            "--host",
            "192.168.0.1",
            "--password",
            "secret",
        ],
        catch_exceptions=False,
    )

    assert result.exit_code != 0
    assert "Unknown metric" in result.output


def test_read_reports_network_error(runner: CliRunner, monkeypatch: pytest.MonkeyPatch) -> None:
    import importlib

    read_mod = importlib.import_module("zte_daemon.cli.commands.read")
    monkeypatch.setattr(read_mod, "ZTEClient", lambda host, **_: NetworkErrorClient())

    result = runner.invoke(
        cli,
        [
            "read",
            "rsrp1",
            "--host",
            "192.168.0.1",
            "--password",
            "secret",
        ],
        catch_exceptions=False,
    )

    assert result.exit_code != 0
    assert "Unable to reach modem" in result.output
