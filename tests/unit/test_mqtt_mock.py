from __future__ import annotations

import json
from pathlib import Path

import pytest

from ..fixtures import load_latest_snapshot
from services.mqtt_mock import MockMQTTBroker


@pytest.fixture()
def snapshot():
    return load_latest_snapshot()


def test_mock_broker_builds_payload(snapshot) -> None:
    broker = MockMQTTBroker(device_id="zte-mc888u-local")
    payload = broker.build_payload(snapshot)
    assert payload["schema_version"] == "0.1.0-mock"
    assert payload["metrics"]["provider"]["value"] == "Telekom"
    assert payload["metrics"]["rsrp"]["value"] == -85
    assert payload["status"] == "mock"


def test_mock_broker_records_publish(tmp_path: Path, snapshot) -> None:
    log_file = tmp_path / "mqtt.jsonl"
    broker = MockMQTTBroker(device_id="zte-mc888u-local", log_path=log_file)
    record = broker.publish(snapshot, topic="zte-modem", broker_host=None)

    assert record.topic == "zte-modem"
    assert record.payload["metrics"]["provider"]["value"] == "Telekom"
    assert log_file.exists()
    lines = log_file.read_text().strip().splitlines()
    assert lines, "expected at least one recorded publish"
    parsed = json.loads(lines[-1])
    assert parsed["topic"] == "zte-modem"
    assert parsed["payload"]["schema_version"] == "0.1.0-mock"
    assert "mock broker defaults" in parsed["notes"]
