from __future__ import annotations

from collections import Counter
from typing import Any

import pytest

from services.metrics_aggregator import MetricsAggregator


class StubClient:
    def __init__(self, payload: dict[str, Any]) -> None:
        self.payload = payload
        self.calls: Counter[str] = Counter()

    def request(self, path: str, *, method: str, expects: str) -> dict[str, Any]:
        self.calls[path] += 1
        return dict(self.payload)


def test_fetch_metric_converts_numeric_values() -> None:
    client = StubClient({"lte_rsrp_1": "-85"})
    aggregator = MetricsAggregator(client)

    value = aggregator.fetch_metric("lte.rsrp1")

    assert value == -85
    assert client.calls  # ensures request executed


def test_collect_lte_filters_missing_entries() -> None:
    payload = {
        "lte_rsrp_1": "-92.0",
        "lte_snr_1": "12.5",
        "lte_rsrq": "-9",
        "lte_rssi": "-70",
        "lte_ca_pcell_freq": "6400",
        "lte_pci": "101",
        "lte_ca_pcell_bandwidth": "10MHz",
    }
    client = StubClient(payload)
    aggregator = MetricsAggregator(client)

    result = aggregator.collect_lte()

    assert result["rsrp1"] == -92.0
    assert result["sinr1"] == 12.5
    assert result["rsrq"] == -9
    assert result["rssi"] == -70
    assert result["earfcn"] == 6400
    assert result["pci"] == 101
    assert result["bw"] == "10MHz"
    assert "rsrp2" not in result


def test_fetch_metric_unknown_identifier() -> None:
    aggregator = MetricsAggregator(StubClient({}))

    with pytest.raises(KeyError):
        aggregator.fetch_metric("nr5g.unknown")
