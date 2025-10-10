from __future__ import annotations

from pathlib import Path

import pytest

from services.modem_mock import MockModemClient, ModemFixtureError

from ..fixtures import load_latest_snapshot


@pytest.fixture()
def client() -> MockModemClient:
    return MockModemClient()


def test_mock_client_loads_fixture(client: MockModemClient) -> None:
    snapshot = client.load_snapshot()
    assert snapshot.timestamp == "2025-10-06T10:00:00Z"
    assert snapshot.rsrp == -85
    assert snapshot.provider == "Telekom"
    assert client.read_metric("RSRP") == -85
    assert client.read_metric("Provider") == "Telekom"


def test_mock_client_requires_monotonic_timestamp(tmp_path: Path, client: MockModemClient) -> None:
    client.load_snapshot()  # establish baseline
    older = tmp_path / "older.json"
    older.write_text(
        """
        {
          "timestamp": "2025-10-05T09:00:00Z",
          "signal": {"rsrp": -90, "sinr": 18},
          "provider": "Telekom"
        }
        """
    )
    with pytest.raises(RuntimeError):
        client.load_snapshot(path=older)


def test_mock_client_raises_helpful_error_on_missing_fixture(tmp_path: Path) -> None:
    missing = tmp_path / "missing.json"
    client = MockModemClient()
    with pytest.raises(ModemFixtureError) as exc:
        client.load_snapshot(path=missing)
    assert "Capture a payload" in str(exc.value)


def test_test_fixture_loader_matches_client() -> None:
    client_snapshot = MockModemClient().load_snapshot()
    fixture_snapshot = load_latest_snapshot()
    assert client_snapshot.rsrp == fixture_snapshot.rsrp
