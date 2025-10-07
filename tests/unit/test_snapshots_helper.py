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


def test_write_snapshot_with_directory_destination_creates_timestamped_file(tmp_path: Path) -> None:
    """Test that directory destination creates timestamped filename."""
    output = write_snapshot({"test": "data"}, tmp_path)
    
    assert output.exists()
    assert output.parent == tmp_path
    assert output.suffix == ".json"
    assert "snapshot.json" in output.name


def test_write_snapshot_with_explicit_filename(tmp_path: Path) -> None:
    """Test that explicit filename is used when provided."""
    output = write_snapshot(
        {"test": "data"},
        tmp_path / "custom-name.json",
    )
    
    assert output.name == "custom-name.json"
    assert output.exists()


def test_write_snapshot_creates_parent_directories(tmp_path: Path) -> None:
    """Test that parent directories are created automatically."""
    nested_path = tmp_path / "level1" / "level2" / "level3" / "snapshot.json"
    output = write_snapshot({"test": "data"}, nested_path)
    
    assert output.exists()
    assert output.parent.parent.parent.exists()


def test_write_snapshot_with_none_metadata(tmp_path: Path) -> None:
    """Test that None metadata is handled gracefully."""
    output = write_snapshot({"test": "data"}, tmp_path / "test.json", metadata=None)
    
    content = json.loads(output.read_text())
    assert "metadata" not in content


def test_write_snapshot_with_complex_data_types(tmp_path: Path) -> None:
    """Test that complex data types are properly serialized."""
    data = {
        "string": "value",
        "integer": 42,
        "float": 3.14,
        "boolean": True,
        "null": None,
        "list": [1, 2, 3],
        "nested": {"key": "value"},
    }
    output = write_snapshot(data, tmp_path / "complex.json")
    
    content = json.loads(output.read_text())
    assert content["data"] == data


def test_write_snapshot_encoding_utf8(tmp_path: Path) -> None:
    """Test that UTF-8 encoding is used for special characters."""
    data = {"message": "Special chars: ñ, é, 中文, emoji 🚀"}
    output = write_snapshot(data, tmp_path / "utf8.json")
    
    content = json.loads(output.read_text(encoding="utf-8"))
    assert "emoji 🚀" in content["data"]["message"]
    assert "中文" in content["data"]["message"]


def test_write_snapshot_includes_captured_at_timestamp(tmp_path: Path) -> None:
    """Test that captured_at timestamp is included."""
    output = write_snapshot({"test": "data"}, tmp_path / "test.json")
    
    content = json.loads(output.read_text())
    assert "captured_at" in content
    # Verify ISO format timestamp
    captured_at = content["captured_at"]
    assert "T" in captured_at
    assert ":" in captured_at


def test_write_snapshot_with_string_destination(tmp_path: Path) -> None:
    """Test that string destinations are properly handled."""
    dest_str = str(tmp_path / "string-dest.json")
    output = write_snapshot({"test": "data"}, dest_str)
    
    assert output.exists()
    assert str(output) == dest_str


def test_write_metric_snapshot_includes_host_in_metadata(
    tmp_path: Path, snapshot: MetricSnapshot
) -> None:
    """Test that host is included in metadata."""
    output = write_metric_snapshot(snapshot, tmp_path / "metric.json")
    
    content = json.loads(output.read_text())
    assert content["metadata"]["host"] == "192.168.0.1"


def test_write_metric_snapshot_includes_timestamp_in_metadata(
    tmp_path: Path, snapshot: MetricSnapshot
) -> None:
    """Test that snapshot timestamp is included in metadata."""
    output = write_metric_snapshot(snapshot, tmp_path / "metric.json")
    
    content = json.loads(output.read_text())
    assert content["metadata"]["captured_at"].startswith("2025-10-06T12:00:00")


def test_write_metric_snapshot_merges_additional_metadata(
    tmp_path: Path, snapshot: MetricSnapshot
) -> None:
    """Test that additional metadata is merged."""
    output = write_metric_snapshot(
        snapshot,
        tmp_path / "metric.json",
        metadata={"custom_key": "custom_value", "source": "test"},
    )
    
    content = json.loads(output.read_text())
    assert content["metadata"]["host"] == "192.168.0.1"
    assert content["metadata"]["custom_key"] == "custom_value"
    assert content["metadata"]["source"] == "test"


def test_serialize_metric_snapshot_includes_all_fields(snapshot: MetricSnapshot) -> None:
    """Test that all fields are included in serialization."""
    payload = serialize_metric_snapshot(snapshot)
    
    assert payload["provider"] == "TestNet"
    assert payload["cell"] == "ABC123"
    assert payload["connection"] == "ENDC"
    assert payload["bands"] == "B20+n28"
    assert payload["wan_ip"] == "203.0.113.5"


def test_serialize_metric_snapshot_temperature_structure(snapshot: MetricSnapshot) -> None:
    """Test temperature readings structure in serialization."""
    payload = serialize_metric_snapshot(snapshot)
    
    temps = payload["temperatures"]
    assert temps["antenna"] == 32
    assert temps["modem"] == 38
    assert temps["power_amplifier"] == 41


def test_serialize_metric_snapshot_lte_structure(snapshot: MetricSnapshot) -> None:
    """Test LTE metrics structure in serialization."""
    payload = serialize_metric_snapshot(snapshot)
    
    lte = payload["lte"]
    assert lte["rsrp"] == [-95, -97]
    assert lte["sinr"] == [18, 16]
    assert lte["rsrq"] == -10
    assert lte["rssi"] == -72
    assert lte["earfcn"] == 1234
    assert lte["pci"] == 200
    assert lte["bandwidth"] == "10MHz"


def test_serialize_metric_snapshot_nr5g_structure(snapshot: MetricSnapshot) -> None:
    """Test NR5G metrics structure in serialization."""
    payload = serialize_metric_snapshot(snapshot)
    
    nr5g = payload["nr5g"]
    assert nr5g["rsrp"] == [-88]
    assert nr5g["sinr"] == 12
    assert nr5g["arfcn"] == 4321
    assert nr5g["pci"] == 400
    assert nr5g["bandwidth"] == "20MHz"


def test_serialize_metric_snapshot_neighbors_structure(snapshot: MetricSnapshot) -> None:
    """Test neighbor cells structure in serialization."""
    payload = serialize_metric_snapshot(snapshot)
    
    neighbors = payload["neighbors"]
    assert len(neighbors) == 1
    assert neighbors[0]["identifier"] == "cell-1"
    assert neighbors[0]["rsrp"] == -105
    assert neighbors[0]["rsrq"] == -14


def test_serialize_metric_snapshot_metrics_map(snapshot: MetricSnapshot) -> None:
    """Test that metrics map is included in serialization."""
    payload = serialize_metric_snapshot(snapshot)
    
    metrics = payload["metrics"]
    assert metrics["provider"] == "TestNet"
    assert metrics["rsrp1"] == -95
    assert metrics["nr5g_rsrp"] == -88


def test_serialize_metric_snapshot_with_empty_neighbors() -> None:
    """Test serialization with no neighbor cells."""
    snapshot = MetricSnapshot(
        timestamp=datetime(2025, 10, 6, 12, 0, tzinfo=timezone.utc),
        host="192.168.0.1",
        provider="Test",
        cell=None,
        connection=None,
        bands=None,
        wan_ip=None,
        temperatures=TemperatureReadings(None, None, None),
        lte=LteMetrics(),
        nr5g=Nr5GMetrics(),
        neighbors=[],
    )
    
    payload = serialize_metric_snapshot(snapshot)
    assert payload["neighbors"] == []


def test_serialize_metric_snapshot_with_multiple_neighbors() -> None:
    """Test serialization with multiple neighbor cells."""
    snapshot = MetricSnapshot(
        timestamp=datetime(2025, 10, 6, 12, 0, tzinfo=timezone.utc),
        host="192.168.0.1",
        provider="Test",
        cell=None,
        connection=None,
        bands=None,
        wan_ip=None,
        temperatures=TemperatureReadings(None, None, None),
        lte=LteMetrics(),
        nr5g=Nr5GMetrics(),
        neighbors=[
            NeighborCell(identifier="cell-1", rsrp=-105, rsrq=-14),
            NeighborCell(identifier="cell-2", rsrp=-110, rsrq=-16),
            NeighborCell(identifier="cell-3", rsrp=-108, rsrq=None),
        ],
    )
    
    payload = serialize_metric_snapshot(snapshot)
    assert len(payload["neighbors"]) == 3
    assert payload["neighbors"][2]["rsrq"] is None


def test_write_snapshot_json_is_pretty_printed(tmp_path: Path) -> None:
    """Test that JSON output is pretty-printed."""
    output = write_snapshot(
        {"key1": "value1", "key2": {"nested": "value"}},
        tmp_path / "pretty.json",
    )
    
    content = output.read_text()
    # Pretty-printed JSON has indentation
    assert "  " in content
    # Keys are on separate lines
    assert content.count("\n") > 2


def test_write_snapshot_json_keys_sorted(tmp_path: Path) -> None:
    """Test that JSON keys are sorted alphabetically."""
    output = write_snapshot(
        {"zebra": 1, "apple": 2, "monkey": 3},
        tmp_path / "sorted.json",
    )
    
    content = output.read_text()
    # Verify apple comes before monkey comes before zebra
    apple_pos = content.index("apple")
    monkey_pos = content.index("monkey")
    zebra_pos = content.index("zebra")
    assert apple_pos < monkey_pos < zebra_pos


def test_write_metric_snapshot_with_directory_creates_timestamped(
    tmp_path: Path, snapshot: MetricSnapshot
) -> None:
    """Test that directory destination creates timestamped file."""
    output = write_metric_snapshot(snapshot, tmp_path)
    
    assert output.exists()
    assert output.parent == tmp_path
    assert "snapshot.json" in output.name


def test_write_snapshot_returns_path_object(tmp_path: Path) -> None:
    """Test that write_snapshot returns a Path object."""
    output = write_snapshot({"test": "data"}, tmp_path / "test.json")
    
    assert isinstance(output, Path)
    assert output.is_file()