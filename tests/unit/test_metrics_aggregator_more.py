from __future__ import annotations

from typing import Any

import pytest

from services.metrics_aggregator import MetricsAggregator


class StubClient:
    def __init__(self, payload: Any) -> None:
        # Accept any object so we can exercise the non-dict error path
        self.payload = payload

    def request(self, path: str, *, method: str, expects: str) -> Any:  # pragma: no cover - simple forwarder
        return self.payload


def test_collect_all_builds_nested_groups_and_coerces_types() -> None:
    payload = {
        # Top-level
        "network_provider_fullname": " Telecom ",
        "cell_id": "abcd",
        "network_type": "ENDC",
        "wan_active_band": "B20 + n28",
        "wan_ipaddr": "10.0.0.2",
        # LTE group
        "lte_rsrp_1": "-90",
        "lte_snr_1": "12.5",
        "lte_rsrq": "-9",
        "lte_rssi": "-70",
        "lte_ca_pcell_freq": "6400",
        "lte_pci": "101",
        "lte_ca_pcell_bandwidth": "10MHz",
        # NR5G group
        "5g_rx0_rsrp": "-95",
        "5g_rx1_rsrp": "",  # empty stays empty string
        "Z5g_SINR": "20.0",
        "nr5g_pci": "123",
        "nr5g_action_channel": "640000",
        # Temp group
        "pm_sensor_ambient": " 40 ",
        "pm_sensor_mdm": "50.0",
        "pm_sensor_pa1": "",  # empty stays empty string
    }
    agg = MetricsAggregator(StubClient(payload))

    out = agg.collect_all()

    # Top-level keys (string coercion trims, leaves non-numeric as string)
    assert out["provider"] == "Telecom"
    assert out["cell"] == "abcd"
    assert out["connection"] == "ENDC"
    assert out["bands"] == "B20 + n28"
    assert out["wan_ip"] == "10.0.0.2"

    # LTE numeric coercions
    assert out["lte"]["rsrp1"] == -90
    assert out["lte"]["sinr1"] == 12.5
    assert out["lte"]["rsrq"] == -9
    assert out["lte"]["rssi"] == -70
    assert out["lte"]["earfcn"] == 6400
    assert out["lte"]["pci"] == 101
    assert out["lte"]["bw"] == "10MHz"

    # NR5G group (includes empty strings when present in payload)
    assert out["nr5g"]["rsrp1"] == -95
    assert out["nr5g"]["rsrp2"] == ""  # empty string preserved
    assert out["nr5g"]["sinr"] == 20.0
    assert out["nr5g"]["pci"] == 123
    assert out["nr5g"]["arfcn"] == 640000

    # Temperature group
    assert out["temp"]["a"] == 40
    assert out["temp"]["m"] == 50.0
    assert out["temp"]["p"] == ""  # empty string preserved


def test_collect_all_handles_missing_values() -> None:
    # Only a couple of fields present; others missing/None
    payload = {
        "network_provider_fullname": None,  # top-level: results in None
        "lte_rsrp_1": "-100",
        # nr5g.* and temp.* all missing
    }
    agg = MetricsAggregator(StubClient(payload))

    out = agg.collect_all()

    # Top-level: missing -> None
    assert out["provider"] is None
    assert out["cell"] is None
    assert out["connection"] is None
    assert out["bands"] is None
    assert out["wan_ip"] is None

    # Only present LTE entry appears
    assert out["lte"] == {"rsrp1": -100}
    # Other groups empty dicts
    assert out["nr5g"] == {}
    assert out["temp"] == {}


def test_collect_nr5g_and_temp_groups() -> None:
    payload = {
        # NR5G subset
        "5g_rx0_rsrp": "-110",
        "Z5g_SINR": "18.5",
        # Temp subset
        "pm_sensor_mdm": "46",
    }
    agg = MetricsAggregator(StubClient(payload))

    nr5g = agg.collect_nr5g()
    temp = agg.collect_temp()

    assert nr5g == {"rsrp1": -110, "sinr": 18.5}
    assert temp == {"m": 46}


def test_fetch_missing_payload_key_raises_keyerror() -> None:
    # Mapped key exists but value is None -> raises KeyError
    payload = {"lte_rsrp_1": None}
    agg = MetricsAggregator(StubClient(payload))
    with pytest.raises(KeyError):
        agg.fetch_metric("lte.rsrp1")


def test_fetch_alias_method_and_coercion_edge_cases() -> None:
    # Exercise string trim/non-numeric, empty string, and non-string passthrough via fetch()
    payload = {
        # Non-numeric string -> returns trimmed string
        "network_provider_fullname": " Foo ",
        # Empty string preserved
        "cell_id": "",
        # Non-string (int) returns unchanged
        "lte_rsrp_1": -101,
    }
    agg = MetricsAggregator(StubClient(payload))

    assert agg.fetch("provider") == "Foo"  # uses fetch alias line
    assert agg.fetch_metric("cell") == ""  # empty preserved
    assert agg.fetch("lte.rsrp1") == -101  # non-string unchanged


def test_load_payload_non_dict_raises_runtime_error() -> None:
    # Client returns a non-dict; _load_payload should reject it
    agg = MetricsAggregator(StubClient(["not", "a", "dict"]))
    with pytest.raises(RuntimeError):
        _ = agg.collect_lte()
