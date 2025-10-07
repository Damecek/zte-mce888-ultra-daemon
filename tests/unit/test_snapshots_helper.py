from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from zte_daemon.lib.snapshots import (
    serialize_metric_snapshot,
    write_metric_snapshot,
    write_snapshot,
)
from zte_daemon.modem.metrics import (
    LteMetrics,
    MetricSnapshot,
    NeighborCell,
    Nr5GMetrics,
    TemperatureReadings,
)


@pytest.fixture()
def snapshot() -> MetricSnapshot:
    """
    Provide a deterministic MetricSnapshot instance populated with representative test data.
    
    The snapshot has a UTC timestamp of 2025-10-06T12:00:00, host "192.168.0.1", provider "TestNet", ENDC connection and example LTE/NR5G metrics, temperatures, and one neighbor cell.
    
    Returns:
        MetricSnapshot: A ready-to-use test snapshot with:
            - host: "192.168.0.1"
            - provider: "TestNet"
            - timestamp: 2025-10-06T12:00:00+00:00
            - temperatures.antenna: 32
            - lte.rsrp: [-95, -97]
            - nr5g.rsrp: [-88]
            - neighbors[0].identifier: "cell-1"
    """
    return MetricSnapshot(
        timestamp=datetime(2025, 10, 6, 12, 0, tzinfo=timezone.utc),
        host="192.168.0.1",
        provider="TestNet",
        cell="ABC123",
        connection="ENDC",
        bands="B20+n28",
        wan_ip="203.0.113.5",
        temperatures=TemperatureReadings(antenna=32, modem=38, power_amplifier=41),
        lte=LteMetrics(
            rsrp=[-95, -97],
            sinr=[18, 16],
            rsrq=-10,
            rssi=-72,
            earfcn=1234,
            pci=200,
            bandwidth="10MHz",
        ),
        nr5g=Nr5GMetrics(
            rsrp=[-88],
            sinr=12,
            arfcn=4321,
            pci=400,
            bandwidth="20MHz",
        ),
        neighbors=[NeighborCell(identifier="cell-1", rsrp=-105, rsrq=-14)],
    )


def test_write_snapshot_creates_json(tmp_path: Path) -> None:
    output = write_snapshot(
        {"status": "ok"},
        tmp_path / "captures",
        metadata={"path": "goform/example"},
    )

    assert output.exists()
    assert output.suffix == ".json"
    content = json.loads(output.read_text())
    assert content["metadata"]["path"] == "goform/example"
    assert content["data"] == {"status": "ok"}


def test_write_metric_snapshot_serializes_data(tmp_path: Path, snapshot: MetricSnapshot) -> None:
    output = write_metric_snapshot(snapshot, tmp_path / "captures" / "snapshot.json")

    content = json.loads(output.read_text())
    assert content["metadata"]["host"] == "192.168.0.1"
    assert content["metadata"]["captured_at"].startswith("2025-10-06T12:00:00")
    data = content["data"]
    assert data["provider"] == "TestNet"
    assert data["lte"]["rsrp"] == [-95, -97]
    assert data["nr5g"]["rsrp"] == [-88]
    assert data["neighbors"][0]["identifier"] == "cell-1"


def test_serialize_metric_snapshot_returns_structure(snapshot: MetricSnapshot) -> None:
    payload = serialize_metric_snapshot(snapshot)
    assert payload["provider"] == "TestNet"
    assert payload["temperatures"]["antenna"] == 32
    assert payload["lte"]["pci"] == 200