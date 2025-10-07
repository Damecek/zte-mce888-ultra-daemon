from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from click.testing import CliRunner
import httpx
import pytest

from zte_daemon.cli.main import cli
from zte_daemon.mqtt.mock_broker import MockMQTTBroker, get_last_record
from zte_daemon.modem.zte_client import RequestError


class SnapshotStub:
    def __init__(self) -> None:
        self.timestamp = datetime(2025, 10, 6, 10, 0, tzinfo=timezone.utc)
        self.rsrp1 = -85
        self.provider = "TestNet"


class ClientStub:
    def __enter__(self) -> "ClientStub":
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        return False

    def login(self, password: str) -> bool:
        return True

    def fetch_snapshot(self) -> SnapshotStub:
        return SnapshotStub()


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


def test_run_command_reports_snapshot_and_records_publish(
    tmp_path: Path, runner: CliRunner, monkeypatch: pytest.MonkeyPatch
) -> None:
    import importlib

    run_mod = importlib.import_module("zte_daemon.cli.commands.run")
    monkeypatch.setattr(run_mod, "ZTEClient", lambda host, **_: ClientStub())
    monkeypatch.setattr(MockMQTTBroker, "_write_record", lambda self, record: None, raising=False)

    log_file = tmp_path / "zte.log"
    result = runner.invoke(
        cli,
        [
            "run",
            "--device-pass",
            "test-pass",
            "--log",
            "info",
            "--log-file",
            str(log_file),
            "--mqtt-host",
            "192.168.0.50:8080",
            "--mqtt-topic",
            "zte-modem",
            "--mqtt-user",
            "user",
            "--mqtt-password",
            "pass",
            "--foreground",
        ],
        catch_exceptions=False,
    )

    assert result.exit_code == 0
    output = result.output
    assert "Fetched metrics for host 192.168.0.1" in output
    assert "RSRP1=-85 dBm" in output
    assert "Provider=TestNet" in output
    record = get_last_record()
    assert record is not None
    assert record.topic == "zte-modem"
    payload = record.payload
    assert payload["schema_version"] == "0.1.0-mock"
    assert payload["metrics"]["rsrp"]["value"] == -85
    assert log_file.exists()
    assert "zte-modem" in log_file.read_text()


def test_run_command_requires_device_password(runner: CliRunner) -> None:
    result = runner.invoke(cli, ["run"], catch_exceptions=False)
    assert result.exit_code != 0
    assert "--device-pass" in result.output


def test_run_reports_network_error(runner: CliRunner, monkeypatch: pytest.MonkeyPatch) -> None:
    import importlib

    run_mod = importlib.import_module("zte_daemon.cli.commands.run")
    monkeypatch.setattr(run_mod, "ZTEClient", lambda host, **_: NetworkErrorClient())

    result = runner.invoke(
        cli,
        [
            "run",
            "--device-pass",
            "secret",
        ],
        catch_exceptions=False,
    )

    assert result.exit_code != 0
    assert "Unable to reach modem" in result.output
