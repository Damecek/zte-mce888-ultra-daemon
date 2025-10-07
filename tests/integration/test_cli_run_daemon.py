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
        """
        Initialize the StubRunClient with a snapshot.
        
        Parameters:
            snapshot (DummySnapshot): Snapshot instance that will be returned by fetch_snapshot().
        """
        self.snapshot = snapshot

    def __enter__(self) -> "StubRunClient":
        """
        Enter the context manager and yield the StubRunClient instance.
        
        Returns:
            self (StubRunClient): The client instance to be used inside the context manager.
        """
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        """
        Indicates whether exceptions raised inside the context manager should be suppressed.
        
        Returns:
            False: do not suppress exceptions; propagate them to the caller.
        """
        return False

    def login(self, password: str) -> bool:
        """
        Simulate a successful login attempt.
        
        Returns:
            `true` to indicate the login was accepted.
        """
        return True

    def fetch_snapshot(self) -> DummySnapshot:
        """
        Return the stored DummySnapshot associated with this client.
        
        Returns:
            The stored DummySnapshot instance.
        """
        return self.snapshot


@pytest.fixture()
def runner() -> CliRunner:
    """
    Provide a fresh Click CliRunner for invoking CLI commands in tests.
    
    Returns:
        CliRunner: A new CliRunner instance for invoking CLI commands and capturing exit code and output.
    """
    return CliRunner()


def test_run_executes_fetch_cycle_and_records_publish(
    runner: CliRunner, monkeypatch: pytest.MonkeyPatch
) -> None:
    """
    Integration test that runs the `run` CLI command, verifies fetched metrics are printed, and ensures the snapshot is published.
    
    Patches the ZTE client to return a predefined DummySnapshot and replaces the MQTT broker publish method to capture its arguments; invokes the CLI with device host, password, and foreground options. Asserts the process exits with code 0, stdout contains the expected host, RSRP1, and provider lines, and the published snapshot object matches the prepared snapshot.
    """
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
        """
        Record a publish attempt by capturing its arguments and returning a PublishRecord.
        
        Parameters:
            snapshot_arg (Any): The snapshot object being published.
            topic (str): MQTT topic to which the snapshot is published.
            broker_host (str | None): Broker host target; None if not specified.
        
        Returns:
            PublishRecord: A record describing the publish (topic, empty payload, broker_host, and empty notes/ timestamps).
        
        """
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