"""Implementation of the `zte read` command (flattened src layout)."""

from __future__ import annotations

import time

import click

from lib.logging_setup import get_logger, logging_options
from lib.options import router_options
from services import zte_client
from services.metrics_aggregator import MetricsAggregator
from services.neighbor_cells import parse_neighbors
from services.zte_paths import neighbors_path


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

    if router_host:
        try:
            client = zte_client.ZTEClient(router_host)
            client.login(router_password)
            aggregator = MetricsAggregator(client, logger)

            def emit_neighbors() -> None:
                # Dedicated fetch for neighbors as it's not part of MetricsAggregator
                path = neighbors_path()
                data = client.request(path, method="GET", expects="json")
                raw = data.get("ngbr_cell_info") if isinstance(data, dict) else None
                neighbors = parse_neighbors(raw)
                if ident_norm == "neighbors":
                    import json as _json

                    click.echo(_json.dumps(neighbors))
                    return
                import re as _re

                m = _re.fullmatch(r"neighbors\[(\d+)\](?:\.(\w+))?", ident_norm)
                if not m:
                    raise click.ClickException(
                        "Unsupported neighbors selector. Use 'neighbors', 'neighbors[0]' or 'neighbors[0].field'."
                    )
                idx = int(m.group(1))
                field = m.group(2)
                if idx < 0 or idx >= len(neighbors):
                    raise click.ClickException(f"Neighbor index out of range: {idx} (available: {len(neighbors)})")
                item = neighbors[idx]
                if field:
                    if field not in item:
                        raise click.ClickException(f"Unknown neighbor field: {field}. Available: {sorted(item.keys())}")
                    click.echo(f"{item[field]}")
                    return
                import json as _json

                click.echo(_json.dumps(item))
                return

            def emit_once() -> None:
                if ident_norm.startswith("neighbors"):
                    emit_neighbors()
                elif ident_norm in {"lte", "nr5g", "temp", "zte"}:
                    if ident_norm == "lte":
                        obj = aggregator.collect_lte()
                    elif ident_norm == "nr5g":
                        obj = aggregator.collect_nr5g()
                    elif ident_norm == "temp":
                        obj = aggregator.collect_temp()
                    else:
                        obj = aggregator.collect_all()
                    import json as _json

                    click.echo(_json.dumps(obj))
                else:
                    value = aggregator.fetch(ident_norm)
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
        except zte_client.ZTEClientError as exc:
            raise click.ClickException(str(exc)) from exc

    # If desired in the future, a dedicated flag can enable reading from
    # cached fixtures explicitly. For now, host/password are required and
    # all reads are live.
