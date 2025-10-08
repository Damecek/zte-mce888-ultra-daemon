"""Implementation of the `zte read` command (flattened src layout)."""

from __future__ import annotations

import click

from lib.logging_setup import get_logger, logging_options
from services import zte_client
from services.modem_mock import MockModemClient, ModemFixtureError


@click.command(
    name="read",
    help="""Read a modem metric from cached telemetry (e.g., RSRP, Provider).

Arguments:
  METRIC  Metric name (RSRP, Provider)""",
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
    """Read a modem metric from cached telemetry (e.g., RSRP, Provider)."""
    logger = get_logger(log_level, log_file)
    live_value: str | int | float | None = None
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
            # Map CLI metric names to response fields
            name = metric.strip().upper()
            if name == "RSRP":
                live_value = (
                    data.get("lte_rsrp_1")
                    or data.get("lte_rsrp")
                    or data.get("lte_rsrp")
                )
            elif name == "PROVIDER":
                live_value = data.get("network_provider_fullname")
            elif name == "PCI":
                live_value = data.get("lte_pci")
            elif name == "LTE_RSRQ":
                live_value = data.get("lte_rsrq")
            elif name in {"WAN_IP", "WAN-IP", "WANIP", "WAN"}:
                live_value = data.get("wan_ipaddr")
            elif name == "CONNECTION":
                live_value = data.get("network_type")
            elif name == "BANDS":
                live_value = data.get("wan_active_band")
            # If we found a live value, emit and return
            if live_value is not None:
                click.echo(f"{metric}: {live_value}")
                return metric
        except zte_client.ZTEClientError as exc:
            raise click.ClickException(str(exc)) from exc

    modem = MockModemClient()
    try:
        snapshot = modem.load_snapshot()
    except ModemFixtureError as exc:
        raise click.ClickException(str(exc)) from exc

    normalized = metric.upper()
    metric_map = snapshot.metric_map
    canonical = {key.upper(): key for key in metric_map}
    if normalized not in canonical:
        raise click.ClickException("Unknown metric. Supported metrics: RSRP, Provider")

    display_key = canonical[normalized]
    value = metric_map[display_key]
    logger.info(f"Read metric from cached snapshot: {display_key}")
    if log_level.lower() == "debug":
        logger.debug(f"Metric value: {display_key}={value}")
    click.echo(f"{display_key}: {value}")
    return display_key
