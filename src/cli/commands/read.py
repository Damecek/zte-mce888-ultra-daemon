"""Implementation of the `zte read` command (flattened src layout)."""
from __future__ import annotations

import click

from lib.logging_setup import configure_logging
from services.modem_mock import MockModemClient, ModemFixtureError


@click.command(
    name="read",
    help="""Read a modem metric from cached telemetry (e.g., RSRP, Provider).

Arguments:
  METRIC  Metric name (RSRP, Provider)"""
)
@click.argument("metric", metavar="METRIC")
@click.option(
    "log_level",
    "--log",
    type=click.Choice(["debug", "info", "warn", "error"], case_sensitive=False),
    default="info",
    show_default=True,
    help="Log level for stdout output",
)
@click.option(
    "log_file",
    "--log-file",
    type=click.Path(path_type=str),
    help="Optional log file destination (ensures parent dir exists).",
)
def read_command(metric: str, log_level: str, log_file: str | None) -> str:
    """Read a modem metric from cached telemetry (e.g., RSRP, Provider)."""
    logger = configure_logging(log_level, log_file)
    modem = MockModemClient()
    try:
        snapshot = modem.load_snapshot()
    except ModemFixtureError as exc:
        raise click.ClickException(str(exc)) from exc

    normalized = metric.upper()
    metric_map = snapshot.metric_map
    canonical = {key.upper(): key for key in metric_map}
    if normalized not in canonical:
        raise click.ClickException(
            "Unknown metric. Supported metrics: RSRP, Provider"
        )

    display_key = canonical[normalized]
    value = metric_map[display_key]
    logger.info(
        "Read metric from cached snapshot",
        extra={"component": "CLI", "context": {"metric": display_key}},
    )
    click.echo(f"{display_key}: {value}")
    return display_key

