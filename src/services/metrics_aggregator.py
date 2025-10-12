from __future__ import annotations

import logging
from typing import Any

from services import zte_client

# Mapping between daemon metric identifiers and modem JSON payload keys.
_METRIC_KEY_MAP: dict[str, str] = {
    # LTE signal metrics
    "lte.rsrp1": "lte_rsrp_1",
    "lte.rsrp2": "lte_rsrp_2",
    "lte.rsrp3": "lte_rsrp_3",
    "lte.rsrp4": "lte_rsrp_4",
    "lte.sinr1": "lte_snr_1",
    "lte.sinr2": "lte_snr_2",
    "lte.sinr3": "lte_snr_3",
    "lte.sinr4": "lte_snr_4",
    "lte.rsrq": "lte_rsrq",
    "lte.rssi": "lte_rssi",
    "lte.earfcn": "lte_ca_pcell_freq",
    "lte.pci": "lte_pci",
    "lte.bw": "lte_ca_pcell_bandwidth",
    # Provider / top level
    "provider": "network_provider_fullname",
    "cell": "cell_id",
    "connection": "network_type",
    "bands": "wan_active_band",
    "wan_ip": "wan_ipaddr",
    # NR/5G metrics
    "nr5g.rsrp1": "5g_rx0_rsrp",
    "nr5g.rsrp2": "5g_rx1_rsrp",
    "nr5g.sinr": "Z5g_SINR",
    "nr5g.pci": "nr5g_pci",
    "nr5g.arfcn": "nr5g_action_channel",
    # Temperature sensors
    "temp.a": "pm_sensor_ambient",
    "temp.m": "pm_sensor_mdm",
    "temp.p": "pm_sensor_pa1",
}

_LTE_OUTPUT_KEYS: dict[str, str] = {
    "rsrp1": "lte.rsrp1",
    "rsrp2": "lte.rsrp2",
    "rsrp3": "lte.rsrp3",
    "rsrp4": "lte.rsrp4",
    "sinr1": "lte.sinr1",
    "sinr2": "lte.sinr2",
    "sinr3": "lte.sinr3",
    "sinr4": "lte.sinr4",
    "rsrq": "lte.rsrq",
    "rssi": "lte.rssi",
    "earfcn": "lte.earfcn",
    "pci": "lte.pci",
    "bw": "lte.bw",
}

# Combine required payload keys for query construction.
_QUERY_FIELDS = sorted({key for key in _METRIC_KEY_MAP.values()})


def _coerce(value: Any) -> Any:
    """
    Attempt to convert string inputs to numeric types while leaving other values unchanged.
    
    If `value` is a string, leading and trailing whitespace are removed; an empty string is returned as-is. If the trimmed string contains a dot, it is converted to a `float`; otherwise an `int` conversion is attempted. If numeric conversion fails, the trimmed string is returned. Non-string inputs are returned unchanged.
    
    Parameters:
        value (Any): The value to coerce.
    
    Returns:
        Any: A `float` or `int` when conversion succeeds, the trimmed `str` when conversion fails or is empty, or the original non-string `value`.
    """
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return text
        try:
            if "." in text:
                return float(text)
            return int(text)
        except ValueError:
            return text
    return value


class MetricsAggregator:
    """Provides single metric lookups and LTE aggregate payloads."""

    def __init__(self, client: zte_client.ZTEClient, logger: logging.Logger | None = None) -> None:
        """
        Initialize the MetricsAggregator with a ZTE client and optional logger.
        
        Parameters:
            logger (logging.Logger | None): Logger to use for internal messages. If omitted, a logger named "zte_daemon.metrics_aggregator" is created and used.
        """
        self._client = client
        self._logger = logger or logging.getLogger("zte_daemon.metrics_aggregator")

    def fetch_metric(self, metric: str) -> Any:
        """
        Fetches a single metric value from the router payload using the daemon metric identifier.
        
        Parameters:
            metric (str): Daemon metric identifier (case-insensitive) to look up in the router payload.
        
        Returns:
            The metric value coerced to an int or float when the string represents a number, otherwise the original value (string or other type).
        
        Raises:
            KeyError: If the metric is not mapped to a payload key or if the payload does not contain the mapped key.
        """
        ident = metric.lower()
        json_key = _METRIC_KEY_MAP.get(ident)
        if json_key is None:
            raise KeyError(metric)
        payload = self._load_payload()
        value = payload.get(json_key)
        if value is None:
            raise KeyError(metric)
        return _coerce(value)

    def fetch(self, metric: str) -> Any:
        """Alias used by the dispatcher for single metric lookups."""

        return self.fetch_metric(metric)

    def collect_lte(self) -> dict[str, Any]:
        """
        Builds an aggregated dictionary of LTE metrics by extracting and coercing values from the router payload.
        
        Missing metrics are skipped and a warning is logged for each absent metric.
        
        Returns:
            dict[str, Any]: Mapping of output metric keys to coerced metric values.
        """
        payload = self._load_payload()
        aggregate: dict[str, Any] = {}
        for output_key, metric_ident in _LTE_OUTPUT_KEYS.items():
            json_key = _METRIC_KEY_MAP[metric_ident]
            raw = payload.get(json_key)
            if raw is None:
                self._logger.warning("Missing LTE metric", extra={"metric": metric_ident})
                continue
            aggregate[output_key] = _coerce(raw)
        return aggregate

    def collect_all(self) -> dict[str, Any]:
        """Collect a nested aggregate for the full 'zte' group.

        Structure:
        {
          "provider": str,
          "cell": str,
          "connection": str,
          "bands": str,
          "wan_ip": str,
          "lte": { ... },
          "nr5g": { ... },
          "temp": { ... },
        }
        """
        payload = self._load_payload()

        def v(key: str) -> Any:
            raw = payload.get(_METRIC_KEY_MAP[key])
            return None if raw is None else _coerce(raw)

        out: dict[str, Any] = {
            "provider": v("provider"),
            "cell": v("cell"),
            "connection": v("connection"),
            "bands": v("bands"),
            "wan_ip": v("wan_ip"),
            "lte": {},
            "nr5g": {},
            "temp": {},
        }

        # LTE group
        for key, ident in _LTE_OUTPUT_KEYS.items():
            raw = payload.get(_METRIC_KEY_MAP[ident])
            if raw is None:
                continue
            out["lte"][key] = _coerce(raw)

        # NR5G group
        for key, ident in (
            ("rsrp1", "nr5g.rsrp1"),
            ("rsrp2", "nr5g.rsrp2"),
            ("sinr", "nr5g.sinr"),
            ("pci", "nr5g.pci"),
            ("arfcn", "nr5g.arfcn"),
        ):
            raw = payload.get(_METRIC_KEY_MAP[ident])
            if raw is None:
                continue
            out["nr5g"][key] = _coerce(raw)

        # Temperature group
        for key, ident in (("a", "temp.a"), ("m", "temp.m"), ("p", "temp.p")):
            raw = payload.get(_METRIC_KEY_MAP[ident])
            if raw is None:
                continue
            out["temp"][key] = _coerce(raw)

        return out

    def collect_nr5g(self) -> dict[str, Any]:
        payload = self._load_payload()
        out: dict[str, Any] = {}
        for key, ident in (
            ("rsrp1", "nr5g.rsrp1"),
            ("rsrp2", "nr5g.rsrp2"),
            ("sinr", "nr5g.sinr"),
            ("pci", "nr5g.pci"),
            ("arfcn", "nr5g.arfcn"),
        ):
            raw = payload.get(_METRIC_KEY_MAP[ident])
            if raw is None:
                continue
            out[key] = _coerce(raw)
        return out

    def collect_temp(self) -> dict[str, Any]:
        payload = self._load_payload()
        out: dict[str, Any] = {}
        for key, ident in (("a", "temp.a"), ("m", "temp.m"), ("p", "temp.p")):
            raw = payload.get(_METRIC_KEY_MAP[ident])
            if raw is None:
                continue
            out[key] = _coerce(raw)
        return out

    def _load_payload(self) -> dict[str, Any]:
        """
        Load the router metrics payload and return it as a mapping from payload keys to values.
        
        Returns:
            dict[str, Any]: Dictionary mapping router JSON payload keys to their values.
        
        Raises:
            RuntimeError: If the router response is not a dictionary.
        """
        metrics_cmd = ",".join(_QUERY_FIELDS)
        path = f"/goform/goform_get_cmd_process?cmd={metrics_cmd}&multi_data=1"
        data = self._client.request(path, method="GET", expects="json")
        if not isinstance(data, dict):
            raise RuntimeError("Unexpected payload type from router")
        return data


__all__ = ["MetricsAggregator"]