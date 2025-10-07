"""Unit tests for metrics module and MetricSnapshot data structures."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from zte_daemon.modem.metrics import (
    LteMetrics,
    MetricSnapshot,
    NeighborCell,
    Nr5GMetrics,
    TemperatureReadings,
    _as_int,
    _split_numbers,
)


class TestHelperFunctions:
    """Test internal helper functions."""

    def test_as_int_converts_valid_integers(self) -> None:
        assert _as_int("42") == 42
        assert _as_int("-100") == -100
        assert _as_int(123) == 123

    def test_as_int_converts_float_strings(self) -> None:
        assert _as_int("3.14") == 3
        assert _as_int("99.9") == 99

    def test_as_int_returns_none_for_invalid_input(self) -> None:
        assert _as_int("not a number") is None
        assert _as_int("") is None
        assert _as_int(None) is None

    def test_as_int_handles_whitespace(self) -> None:
        assert _as_int("  42  ") == 42

    def test_split_numbers_filters_valid_integers(self) -> None:
        result = _split_numbers(["-85", "-87", "invalid", "90", None])
        assert result == [-85, -87, 90]

    def test_split_numbers_with_empty_list(self) -> None:
        result = _split_numbers([])
        assert result == []

    def test_split_numbers_with_all_invalid(self) -> None:
        result = _split_numbers(["invalid", None, "", "not-a-number"])
        assert result == []


class TestTemperatureReadings:
    """Test TemperatureReadings dataclass."""

    def test_temperature_readings_creation(self) -> None:
        temps = TemperatureReadings(antenna=32, modem=38, power_amplifier=41)
        assert temps.antenna == 32
        assert temps.modem == 38
        assert temps.power_amplifier == 41

    def test_temperature_readings_with_none_values(self) -> None:
        temps = TemperatureReadings(antenna=None, modem=None, power_amplifier=None)
        assert temps.antenna is None
        assert temps.modem is None
        assert temps.power_amplifier is None


class TestNeighborCell:
    """Test NeighborCell dataclass."""

    def test_neighbor_cell_creation(self) -> None:
        cell = NeighborCell(identifier="cell-123", rsrp=-95.0, rsrq=-12.0)
        assert cell.identifier == "cell-123"
        assert cell.rsrp == -95.0
        assert cell.rsrq == -12.0

    def test_neighbor_cell_with_none_values(self) -> None:
        cell = NeighborCell(identifier="cell-456", rsrp=None, rsrq=None)
        assert cell.identifier == "cell-456"
        assert cell.rsrp is None
        assert cell.rsrq is None


class TestLteMetrics:
    """Test LteMetrics dataclass."""

    def test_lte_metrics_defaults(self) -> None:
        metrics = LteMetrics()
        assert metrics.rsrp == []
        assert metrics.sinr == []
        assert metrics.rsrq is None
        assert metrics.rssi is None
        assert metrics.earfcn is None
        assert metrics.pci is None
        assert metrics.bandwidth is None

    def test_lte_metrics_with_values(self) -> None:
        metrics = LteMetrics(
            rsrp=[-85, -87],
            sinr=[18, 16],
            rsrq=-10,
            rssi=-72,
            earfcn=1234,
            pci=200,
            bandwidth="10MHz",
        )
        assert metrics.rsrp == [-85, -87]
        assert metrics.sinr == [18, 16]
        assert metrics.rsrq == -10
        assert metrics.rssi == -72
        assert metrics.earfcn == 1234
        assert metrics.pci == 200
        assert metrics.bandwidth == "10MHz"


class TestNr5GMetrics:
    """Test Nr5GMetrics dataclass."""

    def test_nr5g_metrics_defaults(self) -> None:
        metrics = Nr5GMetrics()
        assert metrics.rsrp == []
        assert metrics.sinr is None
        assert metrics.arfcn is None
        assert metrics.pci is None
        assert metrics.bandwidth is None

    def test_nr5g_metrics_with_values(self) -> None:
        metrics = Nr5GMetrics(
            rsrp=[-88, -90],
            sinr=12,
            arfcn=4321,
            pci=400,
            bandwidth="20MHz",
        )
        assert metrics.rsrp == [-88, -90]
        assert metrics.sinr == 12
        assert metrics.arfcn == 4321
        assert metrics.pci == 400
        assert metrics.bandwidth == "20MHz"


class TestMetricSnapshot:
    """Test MetricSnapshot dataclass and methods."""

    @pytest.fixture()
    def sample_snapshot(self) -> MetricSnapshot:
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

    def test_rsrp1_property(self, sample_snapshot: MetricSnapshot) -> None:
        assert sample_snapshot.rsrp1 == -95

    def test_rsrp1_property_with_empty_list(self) -> None:
        snapshot = MetricSnapshot(
            timestamp=datetime.now(timezone.utc),
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
        assert snapshot.rsrp1 is None

    def test_metric_map_structure(self, sample_snapshot: MetricSnapshot) -> None:
        mapping = sample_snapshot.metric_map()
        assert mapping["provider"] == "TestNet"
        assert mapping["bands"] == "B20+n28"
        assert mapping["wan_ip"] == "203.0.113.5"
        assert mapping["rsrp1"] == -95
        assert mapping["rsrp2"] == -97
        assert mapping["sinr1"] == 18
        assert mapping["sinr2"] == 16
        assert mapping["nr5g_rsrp"] == -88
        assert mapping["nr5g_sinr"] == 12
        assert mapping["temp (A/M/P)"] == (32, 38, 41)

    def test_value_for_retrieves_metrics(self, sample_snapshot: MetricSnapshot) -> None:
        assert sample_snapshot.value_for("provider") == "TestNet"
        assert sample_snapshot.value_for("rsrp1") == -95
        assert sample_snapshot.value_for("nr5g_rsrp") == -88

    def test_value_for_case_insensitive(self, sample_snapshot: MetricSnapshot) -> None:
        assert sample_snapshot.value_for("PROVIDER") == "TestNet"
        assert sample_snapshot.value_for("RSRP1") == -95

    def test_value_for_raises_key_error(self, sample_snapshot: MetricSnapshot) -> None:
        with pytest.raises(KeyError):
            sample_snapshot.value_for("nonexistent_metric")

    def test_from_payload_basic_fields(self) -> None:
        payload = {
            "network_provider_fullname": "Telekom",
            "wan_active_band": "B20+n28",
            "wan_ipaddr": "203.0.113.10",
            "network_type": "ENDC",
            "cell_id": "12345",
        }
        snapshot = MetricSnapshot.from_payload("192.168.0.1", payload)
        assert snapshot.provider == "Telekom"
        assert snapshot.bands == "B20+n28"
        assert snapshot.wan_ip == "203.0.113.10"
        assert snapshot.connection == "ENDC"
        assert snapshot.cell == "12345"

    def test_from_payload_lte_metrics(self) -> None:
        payload = {
            "network_provider_fullname": "Test",
            "lte_rsrp_1": "-85",
            "lte_rsrp_2": "-87",
            "lte_rsrp_3": "invalid",
            "lte_rsrp_4": "-90",
            "lte_snr_1": "18",
            "lte_snr_2": "16",
            "lte_snr_3": "14",
            "lte_snr_4": "12",
            "lte_rsrq": "-10",
            "lte_rssi": "-72",
            "lte_ca_pcell_freq": "1234",
            "lte_pci": "200",
            "lte_ca_pcell_bandwidth": "10MHz",
        }
        snapshot = MetricSnapshot.from_payload("192.168.0.1", payload)
        assert snapshot.lte.rsrp == [-85, -87, -90]
        assert snapshot.lte.sinr == [18, 16, 14, 12]
        assert snapshot.lte.rsrq == -10
        assert snapshot.lte.rssi == -72
        assert snapshot.lte.earfcn == 1234
        assert snapshot.lte.pci == 200
        assert snapshot.lte.bandwidth == "10MHz"

    def test_from_payload_nr5g_metrics(self) -> None:
        payload = {
            "network_provider_fullname": "Test",
            "5g_rx0_rsrp": "-88",
            "5g_rx1_rsrp": "-90",
            "Z5g_SINR": "12",
            "nr5g_action_channel": "4321",
            "nr5g_pci": "400",
            "nr_ca_pcell_bandwidth": "20MHz",
        }
        snapshot = MetricSnapshot.from_payload("192.168.0.1", payload)
        assert snapshot.nr5g.rsrp == [-88, -90]
        assert snapshot.nr5g.sinr == 12
        assert snapshot.nr5g.arfcn == 4321
        assert snapshot.nr5g.pci == 400
        assert snapshot.nr5g.bandwidth == "20MHz"

    def test_from_payload_temperature_readings(self) -> None:
        payload = {
            "network_provider_fullname": "Test",
            "pm_sensor_ambient": "32",
            "pm_sensor_mdm": "38",
            "pm_sensor_pa1": "41",
        }
        snapshot = MetricSnapshot.from_payload("192.168.0.1", payload)
        assert snapshot.temperatures.antenna == 32
        assert snapshot.temperatures.modem == 38
        assert snapshot.temperatures.power_amplifier == 41

    def test_from_payload_neighbor_cells(self) -> None:
        payload = {
            "network_provider_fullname": "Test",
            "ngbr_cell_info": "cell-1,-105,-14;cell-2,-110,-16;cell-3,-108,-15",
        }
        snapshot = MetricSnapshot.from_payload("192.168.0.1", payload)
        assert len(snapshot.neighbors) == 3
        assert snapshot.neighbors[0].identifier == "cell-1"
        assert snapshot.neighbors[0].rsrp == -105
        assert snapshot.neighbors[0].rsrq == -14
        assert snapshot.neighbors[1].identifier == "cell-2"
        assert snapshot.neighbors[2].identifier == "cell-3"

    def test_from_payload_neighbor_cells_incomplete_data(self) -> None:
        payload = {
            "network_provider_fullname": "Test",
            "ngbr_cell_info": "cell-1,-105;cell-2",
        }
        snapshot = MetricSnapshot.from_payload("192.168.0.1", payload)
        assert len(snapshot.neighbors) == 2
        assert snapshot.neighbors[0].identifier == "cell-1"
        assert snapshot.neighbors[0].rsrp == -105
        assert snapshot.neighbors[0].rsrq is None
        assert snapshot.neighbors[1].identifier == "cell-2"
        assert snapshot.neighbors[1].rsrp is None

    def test_from_payload_neighbor_cells_empty_string(self) -> None:
        payload = {
            "network_provider_fullname": "Test",
            "ngbr_cell_info": "",
        }
        snapshot = MetricSnapshot.from_payload("192.168.0.1", payload)
        assert snapshot.neighbors == []

    def test_from_payload_neighbor_cells_not_string(self) -> None:
        payload = {
            "network_provider_fullname": "Test",
            "ngbr_cell_info": None,
        }
        snapshot = MetricSnapshot.from_payload("192.168.0.1", payload)
        assert snapshot.neighbors == []

    def test_from_payload_handles_missing_fields(self) -> None:
        payload = {"network_provider_fullname": "Test"}
        snapshot = MetricSnapshot.from_payload("192.168.0.1", payload)
        assert snapshot.provider == "Test"
        assert snapshot.bands is None
        assert snapshot.wan_ip is None
        assert snapshot.lte.rsrp == []
        assert snapshot.nr5g.rsrp == []

    def test_from_payload_handles_none_values(self) -> None:
        payload = {
            "network_provider_fullname": "Test",
            "wan_active_band": None,
            "wan_ipaddr": None,
            "cell_id": None,
        }
        snapshot = MetricSnapshot.from_payload("192.168.0.1", payload)
        assert snapshot.bands is None
        assert snapshot.wan_ip is None
        assert snapshot.cell is None

    def test_from_payload_default_provider_when_missing(self) -> None:
        payload = {}
        snapshot = MetricSnapshot.from_payload("192.168.0.1", payload)
        assert snapshot.provider == "unknown"

    def test_metric_map_with_multiple_rsrp_values(self) -> None:
        snapshot = MetricSnapshot(
            timestamp=datetime.now(timezone.utc),
            host="192.168.0.1",
            provider="Test",
            cell=None,
            connection=None,
            bands=None,
            wan_ip=None,
            temperatures=TemperatureReadings(None, None, None),
            lte=LteMetrics(rsrp=[-85, -87, -89, -91], sinr=[18, 16, 14, 12]),
            nr5g=Nr5GMetrics(),
            neighbors=[],
        )
        mapping = snapshot.metric_map()
        assert mapping["rsrp1"] == -85
        assert mapping["rsrp2"] == -87
        assert mapping["rsrp3"] == -89
        assert mapping["rsrp4"] == -91
        assert mapping["sinr1"] == 18
        assert mapping["sinr2"] == 16
        assert mapping["sinr3"] == 14
        assert mapping["sinr4"] == 12

    def test_metric_map_nr5g_rsrp_none_when_empty(self) -> None:
        snapshot = MetricSnapshot(
            timestamp=datetime.now(timezone.utc),
            host="192.168.0.1",
            provider="Test",
            cell=None,
            connection=None,
            bands=None,
            wan_ip=None,
            temperatures=TemperatureReadings(None, None, None),
            lte=LteMetrics(),
            nr5g=Nr5GMetrics(rsrp=[]),
            neighbors=[],
        )
        mapping = snapshot.metric_map()
        assert mapping["nr5g_rsrp"] is None