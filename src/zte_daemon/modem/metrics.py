"""Structured representations of modem telemetry snapshots."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Iterable, Mapping

__all__ = [
    "TemperatureReadings",
    "NeighborCell",
    "LteMetrics",
    "Nr5GMetrics",
    "MetricSnapshot",
]


def _as_int(value: Any) -> int | None:
    """
    Convert a value to an integer when possible.
    
    Parameters:
        value (Any): Value to convert; converted to a string then parsed as an integer.
    
    Returns:
        int | None: The parsed integer if conversion succeeds, `None` if the value cannot be converted.
    """
    try:
        return int(str(value))
    except (TypeError, ValueError):
        return None


def _split_numbers(values: Iterable[Any]) -> list[int]:
    """
    Collect integer-convertible items from an iterable.
    
    Parameters:
        values (Iterable[Any]): Values to attempt to convert to integers.
    
    Returns:
        list[int]: Integers parsed from `values` in their original order; items that cannot be converted are omitted.
    """
    result: list[int] = []
    for raw in values:
        val = _as_int(raw)
        if val is not None:
            result.append(val)
    return result


@dataclass(slots=True)
class TemperatureReadings:
    antenna: float | None
    modem: float | None
    power_amplifier: float | None


@dataclass(slots=True)
class NeighborCell:
    identifier: str
    rsrp: float | None
    rsrq: float | None


@dataclass(slots=True)
class LteMetrics:
    rsrp: list[int] = field(default_factory=list)
    sinr: list[int] = field(default_factory=list)
    rsrq: float | None = None
    rssi: float | None = None
    earfcn: int | None = None
    pci: int | None = None
    bandwidth: str | None = None


@dataclass(slots=True)
class Nr5GMetrics:
    rsrp: list[int] = field(default_factory=list)
    sinr: float | None = None
    arfcn: int | None = None
    pci: int | None = None
    bandwidth: str | None = None


@dataclass(slots=True)
class MetricSnapshot:
    timestamp: datetime
    host: str
    provider: str
    cell: str | None
    connection: str | None
    bands: str | None
    wan_ip: str | None
    temperatures: TemperatureReadings
    lte: LteMetrics
    nr5g: Nr5GMetrics
    neighbors: list[NeighborCell]

    @property
    def rsrp1(self) -> int | None:
        """
        Return the first LTE RSRP measurement if available.
        
        Returns:
            int: First value from `lte.rsrp` if the list is non-empty, `None` otherwise.
        """
        return self.lte.rsrp[0] if self.lte.rsrp else None

    def metric_map(self) -> dict[str, Any]:
        """
        Builds a flat mapping of key metrics from the snapshot.
        
        The returned dictionary contains top-level fields ("provider", "bands", "wan_ip"), indexed LTE signal entries ("rsrp1", "rsrp2", ... and "sinr1", "sinr2", ...), NR5G summary fields ("nr5g_rsrp" — the first NR5G RSRP if present, otherwise None; "nr5g_sinr"), and a temperature tuple under the key "temp (A/M/P)" representing (antenna, modem, power amplifier).
        
        Returns:
            dict[str, Any]: A mapping from metric name to its current value.
        """
        mapping: dict[str, Any] = {
            "provider": self.provider,
            "bands": self.bands,
            "wan_ip": self.wan_ip,
        }
        for idx, value in enumerate(self.lte.rsrp, start=1):
            mapping[f"rsrp{idx}"] = value
        for idx, value in enumerate(self.lte.sinr, start=1):
            mapping[f"sinr{idx}"] = value
        mapping["nr5g_rsrp"] = self.nr5g.rsrp[0] if self.nr5g.rsrp else None
        mapping["nr5g_sinr"] = self.nr5g.sinr
        mapping["temp (A/M/P)"] = (
            self.temperatures.antenna,
            self.temperatures.modem,
            self.temperatures.power_amplifier,
        )
        return mapping

    def value_for(self, metric: str) -> Any:
        """
        Retrieve a metric value by name from the snapshot's metric map.
        
        Parameters:
        	metric (str): Metric name to look up; lookup is case-insensitive.
        
        Returns:
        	The value associated with the given metric name from the snapshot's metric map.
        
        Raises:
        	KeyError: If the metric name is not present in the metric map.
        """
        normalized = metric.lower()
        data = self.metric_map()
        if normalized in data:
            return data[normalized]
        raise KeyError(metric)

    @classmethod
    def from_payload(cls, host: str, payload: Mapping[str, Any]) -> "MetricSnapshot":
        """
        Constructs a MetricSnapshot from a raw payload mapping and a host identifier.
        
        Parses common fields and nested metric groups from the provided payload:
        - Sets the snapshot timestamp to the current UTC time.
        - Extracts provider name, active bands, WAN IP, connection type, and cell id.
        - Builds LteMetrics by collecting LTE RSRP and SNR values from keys `lte_rsrp_1`..`lte_rsrp_4` and `lte_snr_1`..`lte_snr_4`, and reading optional LTE fields (`lte_rsrq`, `lte_rssi`, `lte_ca_pcell_freq`, `lte_pci`, `lte_ca_pcell_bandwidth`).
        - Builds Nr5GMetrics by collecting 5G RSRP values from `5g_rx0_rsrp` and `5g_rx1_rsrp`, and reading optional NR5G fields (`Z5g_SINR`, `nr5g_action_channel`, `nr5g_pci`, `nr_ca_pcell_bandwidth`).
        - Constructs TemperatureReadings from `pm_sensor_ambient`, `pm_sensor_mdm`, and `pm_sensor_pa1`.
        - Parses neighbors from `ngbr_cell_info`, expecting semicolon-separated entries where each entry is a comma-separated list with identifier, optional rsrp, and optional rsrq.
        
        Parameters:
            host (str): Host identifier associated with the payload.
            payload (Mapping[str, Any]): Raw telemetry mapping containing metric fields.
        
        Returns:
            MetricSnapshot: A populated MetricSnapshot instance reflecting parsed values from the payload.
        """
        timestamp = datetime.now(UTC)
        provider = str(payload.get("network_provider_fullname", "unknown"))
        bands = payload.get("wan_active_band")
        wan_ip = payload.get("wan_ipaddr")
        connection = payload.get("network_type")
        cell = payload.get("cell_id")

        lte_rsrp = _split_numbers(
            payload.get(f"lte_rsrp_{idx}") for idx in range(1, 5)
        )
        lte_sinr = _split_numbers(
            payload.get(f"lte_snr_{idx}") for idx in range(1, 5)
        )
        lte_metrics = LteMetrics(
            rsrp=lte_rsrp,
            sinr=lte_sinr,
            rsrq=_as_int(payload.get("lte_rsrq")),
            rssi=_as_int(payload.get("lte_rssi")),
            earfcn=_as_int(payload.get("lte_ca_pcell_freq")),
            pci=_as_int(payload.get("lte_pci")),
            bandwidth=payload.get("lte_ca_pcell_bandwidth"),
        )

        nr_rsrp_values = [payload.get("5g_rx0_rsrp"), payload.get("5g_rx1_rsrp")]
        nr_metrics = Nr5GMetrics(
            rsrp=_split_numbers(nr_rsrp_values),
            sinr=_as_int(payload.get("Z5g_SINR")),
            arfcn=_as_int(payload.get("nr5g_action_channel")),
            pci=_as_int(payload.get("nr5g_pci")),
            bandwidth=payload.get("nr_ca_pcell_bandwidth"),
        )

        temps = TemperatureReadings(
            antenna=_as_int(payload.get("pm_sensor_ambient")),
            modem=_as_int(payload.get("pm_sensor_mdm")),
            power_amplifier=_as_int(payload.get("pm_sensor_pa1")),
        )

        neighbors: list[NeighborCell] = []
        raw_neighbors = payload.get("ngbr_cell_info")
        if isinstance(raw_neighbors, str) and raw_neighbors:
            for entry in raw_neighbors.split(";"):
                parts = [part for part in entry.split(",") if part]
                if not parts:
                    continue
                identifier = parts[0]
                rsrp = _as_int(parts[1]) if len(parts) > 1 else None
                rsrq = _as_int(parts[2]) if len(parts) > 2 else None
                neighbors.append(NeighborCell(identifier=identifier, rsrp=rsrp, rsrq=rsrq))

        return cls(
            timestamp=timestamp,
            host=host,
            provider=provider,
            cell=str(cell) if cell is not None else None,
            connection=str(connection) if connection is not None else None,
            bands=str(bands) if bands is not None else None,
            wan_ip=str(wan_ip) if wan_ip is not None else None,
            temperatures=temps,
            lte=lte_metrics,
            nr5g=nr_metrics,
            neighbors=neighbors,
        )