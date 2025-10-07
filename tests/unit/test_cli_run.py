from __future__ import annotations

from pathlib import Path

import pytest
from click.testing import CliRunner

from cli.zte import cli
from services.mqtt_mock import get_last_record


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


def test_run_command_emits_greeting_and_records_publish(tmp_path: Path, runner: CliRunner) -> None:
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
    assert "Hello from the ZTE MC888 Ultra mock daemon!" in output
    assert "Modem snapshot timestamp: 2025-10-06T10:00:00Z" in output
    assert "Recorded MQTT payload to mock broker" in output
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
