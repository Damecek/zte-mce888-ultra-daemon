from __future__ import annotations

import json
import logging
import re
from typing import Any

from services import zte_client
from services.metrics_aggregator import MetricsAggregator
from services.neighbor_cells import parse_neighbors
from services.zte_paths import neighbors_path


class MetricLookupError(ValueError):
    """
    Raised when a metric selector cannot be satisfied.

    Examples include unsupported neighbor selectors, indexes outside the
    available range, or missing fields on neighbor entries.
    """


def fetch_metric_snapshot(
    metric: str,
    *,
    router_host: str,
    router_password: str,
    logger: logging.Logger | None = None,
) -> Any:
    """
    Fetch the current value for the requested metric directly from the router.

    This helper encapsulates the common flow used by both the `read` CLI
    command and the MQTT daemon:

        1. Construct a fresh ZTE client for the configured host.
        2. Authenticate using the provided password.
        3. Use ``MetricsAggregator`` to collect the metric payload.

    Parameters:
        metric (str): Metric identifier supplied by the user/requester.
        router_host (str): Router hostname/IP.
        router_password (str): Authentication password.
        logger (logging.Logger | None): Optional logger to pass through to the
            aggregator for consistency with the daemon log output.

    Returns:
        Any: The resolved metric value. Aggregates (lte/nr5g/temp/zte) return
        dictionaries, neighbor roots produce lists, and scalar metrics yield
        numbers or strings.

    Raises:
        KeyError: When the metric is unknown to ``MetricsAggregator``.
        MetricLookupError: When a neighbor selector is invalid or out of range.
        zte_client.ZTEClientError: When authentication or router communication
            fails.
    """

    ident = metric.strip()
    ident_norm = ident.lower()

    client = zte_client.ZTEClient(router_host)
    try:
        client.login(router_password)
        aggregator = MetricsAggregator(client, logger)

        if ident_norm.startswith("neighbors"):
            return _fetch_neighbors(client, ident_norm)
        if ident_norm == "lte":
            return aggregator.collect_lte()
        if ident_norm == "nr5g":
            return aggregator.collect_nr5g()
        if ident_norm == "temp":
            return aggregator.collect_temp()
        if ident_norm == "zte":
            return aggregator.collect_all()
        return aggregator.fetch(ident_norm)
    finally:
        # Ensure connections are torn down promptly; the helper always uses a
        # short-lived client.
        try:
            client.close()
        except AttributeError:
            # Tests sometimes substitute lightweight stubs without `close`.
            pass


def _fetch_neighbors(client: zte_client.ZTEClient, ident_norm: str) -> Any:
    """
    Resolve neighbor selector requests into structured data.

    Parameters:
        client (zte_client.ZTEClient): Authenticated client.
        ident_norm (str): Lower-cased metric selector; expected to start with
            "neighbors".

    Returns:
        Any: A list of neighbor entries, a single neighbor dict, or the value
        of a specific neighbor field depending on the selector.
    """

    path = neighbors_path()
    data = client.request(path, method="GET", expects="json")
    raw = data.get("ngbr_cell_info") if isinstance(data, dict) else None
    neighbors = parse_neighbors(raw)

    if ident_norm == "neighbors":
        return neighbors

    match = re.fullmatch(r"neighbors\[(\d+)\](?:\.(\w+))?", ident_norm)
    if not match:
        raise MetricLookupError(
            "Unsupported neighbors selector. Use 'neighbors', 'neighbors[0]' or 'neighbors[0].field'."
        )

    index = int(match.group(1))
    field = match.group(2)

    if index < 0 or index >= len(neighbors):
        raise MetricLookupError(f"Neighbor index out of range: {index} (available: {len(neighbors)})")

    entry = neighbors[index]
    if field is None:
        return entry

    if field not in entry:
        raise MetricLookupError(
            f"Unknown neighbor field: {field}. Available fields: {json.dumps(sorted(entry.keys()))}"
        )

    return entry[field]


__all__ = ["MetricLookupError", "fetch_metric_snapshot"]
