from __future__ import annotations

import logging
from collections.abc import Iterable
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from lib.value_coerce import coerce_number_like as _coerce
from services.connected_devices import parse_connected_devices
from services.neighbor_cells import parse_neighbors
from services.zte_paths import connected_devices_path

if TYPE_CHECKING:  # pragma: no cover - typing helper
    from services.zte_client import ZTEClient


@dataclass(frozen=True)
class MetricLeaf:
    """Leaf describing a single modem payload key with optional identifier aliases."""

    payload: str
    aliases: tuple[str, ...] = ()


MetricTree = dict[str, "MetricTree | MetricLeaf"]


class MetricRegistry:
    """Builds a canonical index of metric identifiers and their payload keys."""

    def __init__(self, tree: MetricTree) -> None:
        self._leaves: dict[str, MetricLeaf] = {}
        self._aliases: dict[str, str] = {}
        self._leaf_children: dict[str, dict[str, str]] = {}
        self._build(tree)

    def _build(self, tree: MetricTree, prefix: tuple[str, ...] = ()) -> None:
        parent = ".".join(prefix).lower()
        self._leaf_children.setdefault(parent, {})
        for key, node in tree.items():
            path = (*prefix, key)
            canonical = ".".join(path).lower()
            if isinstance(node, MetricLeaf):
                if canonical in self._leaves:
                    raise ValueError(f"Duplicate metric definition for '{canonical}'")
                self._leaves[canonical] = node
                self._leaf_children[parent][key] = canonical
                for alias in node.aliases:
                    alias_key = alias.lower()
                    existing = self._aliases.get(alias_key)
                    if existing and existing != canonical:
                        raise ValueError(f"Alias '{alias}' reused for '{canonical}' and '{existing}'")
                    self._aliases[alias_key] = canonical
            else:
                self._build(node, path)

    def payload_for(self, metric: str) -> str:
        """Return the modem payload key for the given metric identifier or alias."""

        canonical = self.resolve(metric)
        return self._leaves[canonical].payload

    def resolve(self, metric: str) -> str:
        """Map a metric identifier or alias to its canonical (lowercase) path."""

        ident = metric.lower()
        if ident in self._leaves:
            return ident
        alias = self._aliases.get(ident)
        if alias:
            return alias
        raise KeyError(metric)

    def direct_children(self, group: str) -> dict[str, str]:
        """Return immediate leaf children for a metric group."""

        ident = group.lower()
        children = self._leaf_children.get(ident)
        if not children:
            return {}
        # Filter child entries to those that are leaves (may include nested nodes)
        return {key: canonical for key, canonical in children.items() if canonical in self._leaves}

    def payload_keys(self) -> Iterable[str]:
        return (leaf.payload for leaf in self._leaves.values())


_METRIC_TREE: MetricTree = {
    "provider": MetricLeaf("network_provider_fullname", aliases=("provider.fullname",)),
    "cell": MetricLeaf("cell_id"),
    "connection": MetricLeaf("network_type"),
    "wan": {
        "active": {
            "band": MetricLeaf(
                "wan_active_band",
                aliases=("bands", "wan_active_band", "wan.active.band"),
            ),
            "channel": MetricLeaf("wan_active_channel", aliases=("wan_active_channel",)),
        },
        "apn": MetricLeaf("wan_apn", aliases=("wan_apn",)),
        "ip": MetricLeaf("wan_ipaddr", aliases=("wan_ip", "wan.ipaddr")),
        "lte_ca": MetricLeaf("wan_lte_ca", aliases=("wan_lte_ca",)),
    },
    "bandwidth": MetricLeaf("bandwidth"),
    "dns": {
        "mode": MetricLeaf("dns_mode", aliases=("dns_mode",)),
        "prefer_manual": MetricLeaf("prefer_dns_manual", aliases=("prefer_dns_manual",)),
        "standby_manual": MetricLeaf("standby_dns_manual", aliases=("standby_dns_manual",)),
    },
    "ip_passthrough": MetricLeaf("ip_passthrough_enabled", aliases=("ip_passthrough_enabled",)),
    "rmcc": MetricLeaf("rmcc"),
    "rmnc": MetricLeaf("rmnc"),
    "tx_power": MetricLeaf("tx_power"),
    "neighbors": {
        "raw": MetricLeaf("ngbr_cell_info", aliases=("ngbr_cell_info",)),
    },
    "lte": {
        "band": MetricLeaf("lte_band", aliases=("lte_band",)),
        "rsrp": MetricLeaf("lte_rsrp", aliases=("lte_rsrp",)),
        "rsrp1": MetricLeaf("lte_rsrp_1"),
        "rsrp2": MetricLeaf("lte_rsrp_2"),
        "rsrp3": MetricLeaf("lte_rsrp_3"),
        "rsrp4": MetricLeaf("lte_rsrp_4"),
        "sinr": MetricLeaf("lte_snr", aliases=("lte_snr",)),
        "sinr1": MetricLeaf("lte_snr_1"),
        "sinr2": MetricLeaf("lte_snr_2"),
        "sinr3": MetricLeaf("lte_snr_3"),
        "sinr4": MetricLeaf("lte_snr_4"),
        "rsrq": MetricLeaf("lte_rsrq"),
        "rssi": MetricLeaf("lte_rssi"),
        "earfcn": MetricLeaf("lte_ca_pcell_freq", aliases=("lte.ca.pcell.freq", "lte_ca_pcell_freq")),
        "pci": MetricLeaf("lte_pci"),
        "pci_lock": MetricLeaf("lte_pci_lock", aliases=("lte_pci_lock",)),
        "earfcn_lock": MetricLeaf("lte_earfcn_lock", aliases=("lte_earfcn_lock",)),
        "bw": MetricLeaf(
            "lte_ca_pcell_bandwidth",
            aliases=("lte.ca.pcell.bandwidth", "lte_ca_pcell_bandwidth"),
        ),
        "ca": {
            "pcell": {
                "band": MetricLeaf("lte_ca_pcell_band"),
                "freq": MetricLeaf("lte_ca_pcell_freq"),
                "bandwidth": MetricLeaf("lte_ca_pcell_bandwidth"),
            },
            "scell": {
                "band": MetricLeaf("lte_ca_scell_band"),
                "bandwidth": MetricLeaf("lte_ca_scell_bandwidth"),
                "info": MetricLeaf("lte_multi_ca_scell_info"),
                "signal_info": MetricLeaf("lte_multi_ca_scell_sig_info"),
            },
        },
    },
    "nr5g": {
        "rsrp": MetricLeaf("Z5g_rsrp"),
        "rsrq": MetricLeaf("Z5g_rsrq"),
        "rsrp1": MetricLeaf("5g_rx0_rsrp"),
        "rsrp2": MetricLeaf("5g_rx1_rsrp"),
        "sinr": MetricLeaf("Z5g_SINR"),
        "pci": MetricLeaf("nr5g_pci"),
        "arfcn": MetricLeaf("nr5g_action_channel", aliases=("nr5g.action.channel",)),
        "cell_id": MetricLeaf("nr5g_cell_id"),
        "action": {
            "band": MetricLeaf("nr5g_action_band"),
            "channel": MetricLeaf("nr5g_action_channel", aliases=("nr5g.arfcn",)),
            "nsa_band": MetricLeaf("nr5g_action_nsa_band"),
        },
        "lock": {
            "nsa_band": MetricLeaf("nr5g_nsa_band_lock"),
            "sa_band": MetricLeaf("nr5g_sa_band_lock"),
        },
        "ca": {
            "pcell": {
                "band": MetricLeaf("nr_ca_pcell_band"),
                "freq": MetricLeaf("nr_ca_pcell_freq"),
            },
            "scell": {
                "info": MetricLeaf("nr_multi_ca_scell_info"),
            },
        },
    },
    "wcdma": {
        "rscp1": MetricLeaf("rscp_1"),
        "rscp2": MetricLeaf("rscp_2"),
        "rscp3": MetricLeaf("rscp_3"),
        "rscp4": MetricLeaf("rscp_4"),
        "ecio1": MetricLeaf("ecio_1"),
        "ecio2": MetricLeaf("ecio_2"),
        "ecio3": MetricLeaf("ecio_3"),
        "ecio4": MetricLeaf("ecio_4"),
    },
    "temp": {
        "a": MetricLeaf("pm_sensor_ambient"),
        "m": MetricLeaf("pm_sensor_mdm"),
        "p": MetricLeaf("pm_sensor_pa1"),
        "5g": MetricLeaf("pm_sensor_5g"),
    },
    "wifi": {
        "chip_temp": MetricLeaf("wifi_chip_temp"),
    },
}


_METRICS = MetricRegistry(_METRIC_TREE)
_QUERY_FIELDS = sorted(set(_METRICS.payload_keys()))


class MetricsAggregator:
    """Provides single metric lookups and LTE aggregate payloads."""

    def __init__(self, client: ZTEClient, logger: logging.Logger | None = None) -> None:
        """
        Initialize the MetricsAggregator with a ZTE client and optional logger.

        Parameters:
            logger (logging.Logger | None): Logger for internal messages. If
                omitted, a logger named "zte_daemon.metrics_aggregator" is
                used.
        """
        self._client = client
        self._logger = logger or logging.getLogger("zte_daemon.metrics_aggregator")

    def fetch_metric(self, metric: str) -> Any:
        """
        Fetches a single metric value from the router payload using the daemon metric identifier.

        Parameters:
            metric (str): Daemon metric identifier (case-insensitive) to look up in the router payload.

        Returns:
            The metric value coerced to an int or float when the string
            represents a number; otherwise the original value.

        Raises:
            KeyError: If the metric is not mapped to a payload key or if the payload does not contain the mapped key.
        """
        canonical = _METRICS.resolve(metric)
        json_key = _METRICS.payload_for(canonical)
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
        for output_key, canonical in _METRICS.direct_children("lte").items():
            json_key = _METRICS.payload_for(canonical)
            raw = payload.get(json_key)
            if raw is None:
                self._logger.warning(f"Missing LTE metric: metric={canonical}")
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

        def optional(metric_ident: str) -> Any:
            canonical = _METRICS.resolve(metric_ident)
            raw = payload.get(_METRICS.payload_for(canonical))
            return None if raw is None else _coerce(raw)

        out: dict[str, Any] = {
            "provider": optional("provider"),
            "cell": optional("cell"),
            "connection": optional("connection"),
            "bands": optional("bands"),
            "wan_ip": optional("wan_ip"),
            "lte": self._collect_group(payload, "lte"),
            "nr5g": self._collect_group(payload, "nr5g"),
            "temp": self._collect_group(payload, "temp"),
            "neighbors": self._collect_neighbors(payload),
            "connected_devices": self.collect_connected_devices(),
        }

        return out

    def collect_nr5g(self) -> dict[str, Any]:
        payload = self._load_payload()
        return self._collect_group(payload, "nr5g")

    def collect_temp(self) -> dict[str, Any]:
        payload = self._load_payload()
        return self._collect_group(payload, "temp")

    def _collect_group(self, payload: dict[str, Any], group: str) -> dict[str, Any]:
        out: dict[str, Any] = {}
        for key, canonical in _METRICS.direct_children(group).items():
            raw = payload.get(_METRICS.payload_for(canonical))
            if raw is None:
                continue
            out[key] = _coerce(raw)
        return out

    def _collect_neighbors(self, payload: dict[str, Any]) -> list[dict[str, Any]]:
        raw_key = _METRICS.payload_for("neighbors.raw")
        raw_value = payload.get(raw_key)
        return parse_neighbors(raw_value)

    def collect_connected_devices(self) -> list[dict[str, Any]]:
        response = self._client.request(connected_devices_path(), method="GET", expects="json")
        devices_payload = response.get("lan_station_list") if isinstance(response, dict) else None
        return parse_connected_devices(devices_payload)

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
