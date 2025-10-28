"""Implementation of the `zte read` command (flattened src layout)."""

from __future__ import annotations

import json
import time

import click

from lib.logging_setup import get_logger, logging_options
from lib.options import router_options
from services import zte_client
from services.metric_resolver import MetricLookupError, fetch_metric_snapshot


@click.command(
    name="read",
    help="""Read a router metric by identifier.

Arguments:
  METRIC  Metric identifier (e.g., lte.rsrp1, nr5g.pci, wan_ip).

Identifiers use dot-paths with optional array indices, for example:
  lte.rsrp1, nr5g.rsrp2, temp.a, neighbors[0].id

See docs/metrics.md for the full catalog and naming rules.""",
)
@click.argument("metric", metavar="METRIC")
@router_options()
@logging_options(help_text="Log level for stdout output")
@click.option(
    "--listen",
    is_flag=True,
    help="Continuously read the metric every second until interrupted.",
)
def read_command(
    metric: str,
    router_host: str,
    router_password: str,
    log_level: str,
    log_file: str | None,
    listen: bool,
) -> str:
    """Read a router metric from the router via REST.

    Accepts identifiers like 'lte.rsrp1', 'nr5g.pci', 'wan_ip', 'temp.a'.
    """
    logger = get_logger(log_level, log_file)
    ident = metric.strip()
    ident_norm = ident.lower()

    # All reads are performed live against the router.

    def emit_once() -> None:
        try:
            value = fetch_metric_snapshot(
                ident,
                router_host=router_host,
                router_password=router_password,
                logger=logger,
            )
        except MetricLookupError as exc:
            raise click.ClickException(str(exc)) from exc
        except KeyError as exc:
            raise click.ClickException(str(exc)) from exc
        except zte_client.ZTEClientError as exc:
            raise click.ClickException(str(exc)) from exc

        if isinstance(value, (dict, list)):
            click.echo(json.dumps(value))
        elif ident_norm.startswith("neighbors"):
            click.echo(f"{value}")
        else:
            click.echo(f"{ident}: {value}")

    if listen:
        try:
            while True:
                emit_once()
                time.sleep(1)
        except KeyboardInterrupt:
            return ident
    else:
        emit_once()
        return ident
