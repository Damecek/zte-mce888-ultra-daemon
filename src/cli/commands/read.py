"""Implementation of the `zte read` command (flattened src layout)."""

from __future__ import annotations
from multiprocessing import Lock

import click

from lib.logging_setup import get_logger, logging_options
from services import zte_client
from services.modem_mock import MockModemClient, ModemFixtureError


@click.command(
    name="read",
    help="""Read a modem metric by identifier.

Arguments:
  METRIC  Metric identifier (e.g., lte.rsrp1, nr5g.pci, wan_ip).

Identifiers use dot-paths with optional array indices, for example:
  lte.rsrp1, nr5g.rsrp2, temp.a, neighbors[0].id

See docs/metrics.md for the full catalog and naming rules.""",
)
@click.argument("metric", metavar="METRIC")
@click.option("--host", help="Modem host URL (use REST client when provided)")
@click.option("--password", help="Modem admin password (required with --host)")
@logging_options(help_text="Log level for stdout output")
def read_command(
    metric: str,
    host: str | None,
    password: str | None,
    log_level: str,
    log_file: str | None,
) -> str:
    """Read a modem metric from live REST (when --host given) or cached fixture.

    Accepts identifiers like 'lte.rsrp1', 'nr5g.pci', 'wan_ip', 'temp.a'.
    """
    logger = get_logger(log_level, log_file)
    ident = metric.strip()
    ident_norm = ident.lower()

    # Mapping helpers for live REST responses (flat JSON keys)
    # Keys come from js_implementation.js (siginfo) and modem UI
    LIVE_MAP: dict[str, str] = {
        # LTE signal
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
        "lte.pci": "lte_pci",
        # Best-effort: primary EARFCN frequency
        "lte.earfcn": "lte_ca_pcell_freq",
        # Band summary from WAN
        "lte.bw": "lte_ca_pcell_bandwidth",
        # NR/5G signal
        "nr5g.rsrp1": "5g_rx0_rsrp",
        "nr5g.rsrp2": "5g_rx1_rsrp",
        "nr5g.sinr": "Z5g_SINR",
        "nr5g.pci": "nr5g_pci",
        "nr5g.arfcn": "nr5g_action_channel",
        # Top-level context
        "provider": "network_provider_fullname",
        "cell": "cell_id",
        "connection": "network_type",
        "bands": "wan_active_band",
        "wan_ip": "wan_ipaddr",
        # Temperatures
        "temp.a": "pm_sensor_ambient",
        "temp.m": "pm_sensor_mdm",
        "temp.p": "pm_sensor_pa1",
    }

    def _to_num(val: str) -> int | float | str:
        try:
            if "." in val:
                return float(val)
            return int(val)
        except Exception:
            return val

    def _parse_neighbors(raw: object | None) -> list[dict[str, object]]:
        if not raw:
            return []
        items: list[dict[str, object]] = []
        # Format: "freq,pci,rsrq,rsrp,rssi;freq,pci,rsrq,rsrp,rssi;..."
        for cell in str(raw).split(";"):
            if not cell:
                continue
            parts = cell.split(",")
            if len(parts) < 5:
                # Ignore malformed entries
                continue
            freq, pci, rsrq, rsrp, rssi = parts[:5]
            obj = {
                "id": _to_num(pci),
                "rsrp": _to_num(rsrp),
                "rsrq": _to_num(rsrq),
                "freq": _to_num(freq),
                "rssi": _to_num(rssi),
            }
            items.append(obj)
        return items

    # Subset mapping against the mock fixture payload (tests/fixtures/modem/latest.json)
    # We fall back to these when --host is not provided
    def read_from_mock_payload(payload: dict) -> tuple[bool, object | None]:
        # Limited set available in the current test fixture
        if ident_norm in {"lte.rsrp", "rsrp", "lte.rsrp1"}:
            return True, payload.get("signal", {}).get("rsrp")
        if ident_norm in {
            "nr5g.sinr",
            "sinr",
        }:  # preserve basic name for backward compat in fixture
            return True, payload.get("signal", {}).get("sinr")
        if ident_norm in {"provider"}:
            return True, payload.get("provider")
        if ident_norm in {"wan_ip", "network.ipv4"}:
            return True, payload.get("network", {}).get("ipv4")
        # Not available in the minimal mock fixture
        return False, None

    live_value: object | None = None
    if host:
        if not password:
            raise click.ClickException("--password is required when using --host")
        try:
            client = zte_client.ZTEClient(host)
            client.login(password)
            # Comprehensive metrics fetch (multi_data=1) derived from docs/discover/metrics.md
            metrics_cmd = (
                "wan_active_band,wan_active_channel,wan_lte_ca,wan_apn,wan_ipaddr,"
                "cell_id,dns_mode,prefer_dns_manual,standby_dns_manual,network_type,"
                "network_provider_fullname,rmcc,rmnc,ip_passthrough_enabled,bandwidth,tx_power,"
                "rscp_1,ecio_1,rscp_2,ecio_2,rscp_3,ecio_3,rscp_4,ecio_4,ngbr_cell_info,"
                "lte_multi_ca_scell_info,lte_multi_ca_scell_sig_info,lte_band,lte_rsrp,lte_rsrq,"
                "lte_rsrq,lte_rssi,lte_rsrp,lte_snr,lte_ca_pcell_band,lte_ca_pcell_freq,"
                "lte_ca_pcell_bandwidth,lte_ca_scell_band,lte_ca_scell_bandwidth,lte_rsrp_1,"
                "lte_rsrp_2,lte_rsrp_3,lte_rsrp_4,lte_snr_1,lte_snr_2,lte_snr_3,lte_snr_4,lte_pci,"
                "lte_pci_lock,lte_earfcn_lock,5g_rx0_rsrp,5g_rx1_rsrp,Z5g_rsrp,Z5g_rsrq,Z5g_SINR,"
                "nr5g_cell_id,nr5g_pci,nr5g_action_channel,nr5g_action_band,nr5g_action_nsa_band,"
                "nr_ca_pcell_band,nr_ca_pcell_freq,nr_multi_ca_scell_info,nr5g_sa_band_lock,"
                "nr5g_nsa_band_lock,pm_sensor_ambient,pm_sensor_mdm,pm_sensor_5g,pm_sensor_pa1,wifi_chip_temp"
            )
            path = f"/goform/goform_get_cmd_process?cmd={metrics_cmd}&multi_data=1"
            data = client.request(path, method="GET", expects="json")
            logger.debug(f"Received data: {data}")

            # Neighbors: map to ngbr_cell_info → parsed list of objects
            if ident_norm.startswith("neighbors"):
                raw = data.get("ngbr_cell_info")
                neighbors = _parse_neighbors(raw)
                if ident_norm == "neighbors":
                    import json as _json
                    click.echo(_json.dumps(neighbors))
                    return ident

                import re as _re
                m = _re.fullmatch(r"neighbors\[(\d+)\](?:\.(\w+))?", ident_norm)
                if not m:
                    raise click.ClickException(
                        "Unsupported neighbors selector. Use 'neighbors', 'neighbors[0]' or 'neighbors[0].field'."
                    )
                idx = int(m.group(1))
                field = m.group(2)
                if idx < 0 or idx >= len(neighbors):
                    raise click.ClickException(
                        f"Neighbor index out of range: {idx} (available: {len(neighbors)})"
                    )
                item = neighbors[idx]
                if field:
                    if field not in item:
                        raise click.ClickException(
                            f"Unknown neighbor field: {field}. Available: {sorted(item.keys())}"
                        )
                    click.echo(f"{item[field]}")
                    return ident
                import json as _json
                click.echo(_json.dumps(item))
                return ident

            # Resolve identifier using LIVE_MAP
            json_key = LIVE_MAP.get(ident_norm)
            if json_key is None:
                raise click.ClickException(
                    f"Unknown metric identifier: {ident}. See docs/metrics.md for supported identifiers."
                )
            live_value = data.get(json_key)
            if live_value is None:
                raise click.ClickException(
                    f"No value for '{ident}' in modem response (missing '{json_key}')."
                )
            click.echo(f"{ident}: {live_value}")
            return ident
        except zte_client.ZTEClientError as exc:
            raise click.ClickException(str(exc)) from exc

    modem = MockModemClient()
    try:
        snapshot = modem.load_snapshot()
    except ModemFixtureError as exc:
        raise click.ClickException(str(exc)) from exc

    ok, value = read_from_mock_payload(snapshot.raw_payload)
    if not ok:
        raise click.ClickException(
            "Unknown metric identifier for mock data. Supported examples: "
            "lte.rsrp1, nr5g.sinr, provider, wan_ip"
        )

    logger.info(f"Read metric from cached snapshot: {ident}")
    if log_level.lower() == "debug":
        logger.debug(f"Metric value: {ident}={value}")
    click.echo(f"{ident}: {value}")
    return ident
