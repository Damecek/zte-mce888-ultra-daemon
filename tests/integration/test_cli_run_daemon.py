"""Integration test for the refreshed `zte run` command."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from click.testing import CliRunner
import pytest

from zte_daemon.cli.main import cli
from zte_daemon.mqtt.mock_broker import PublishRecord


@dataclass(slots=True)
class DummySnapshot:
    timestamp: datetime
    host: str
    rsrp1: int
    provider: str


class StubRunClient:
    def __init__(self, snapshot: DummySnapshot) -> None:
        self.snapshot = snapshot

    def __enter__(self) -> "StubRunClient":
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        return False

    def login(self, password: str) -> bool:
        return True

    def fetch_snapshot(self) -> DummySnapshot:
        return self.snapshot


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


def test_run_executes_fetch_cycle_and_records_publish(
    runner: CliRunner, monkeypatch: pytest.MonkeyPatch
) -> None:
    snapshot = DummySnapshot(
        timestamp=datetime(2025, 10, 6, 10, 0, tzinfo=timezone.utc),
        host="192.168.0.1",
        rsrp1=-85,
        provider="TestNet",
    )

    import importlib

    run_mod = importlib.import_module("zte_daemon.cli.commands.run")
    monkeypatch.setattr(run_mod, "ZTEClient", lambda host, **_: StubRunClient(snapshot))

    published: dict[str, Any] = {}

    def record_publish(self, snapshot_arg: Any, *, topic: str, broker_host: str | None):
        published.update({"snapshot": snapshot_arg, "topic": topic, "broker_host": broker_host})
        return PublishRecord(
            topic=topic,
            payload={},
            broker_host=broker_host,
            notes="",
            published_at="",
        )

    monkeypatch.setattr(run_mod.MockMQTTBroker, "publish", record_publish, raising=False)

    result = runner.invoke(
        cli,
        [
            "run",
            "--device-host",
            "192.168.0.1",
            "--device-pass",
            "secret",
            "--foreground",
        ],
        catch_exceptions=False,
    )

    assert result.exit_code == 0
    output = result.output
    assert "Fetched metrics for host 192.168.0.1" in output
    assert "RSRP1=-85 dBm" in output
    assert "Provider=TestNet" in output
    assert published["snapshot"] is snapshot
