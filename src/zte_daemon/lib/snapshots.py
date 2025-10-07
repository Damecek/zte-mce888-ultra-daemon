"""Utilities for persisting modem snapshots and discover payloads."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Mapping

from zte_daemon.modem.metrics import MetricSnapshot

__all__ = ["write_snapshot", "serialize_metric_snapshot", "write_metric_snapshot"]


def _resolve_destination(destination: str | Path) -> Path:
    path = Path(destination)
    if path.suffix:
        return path
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    return path / f"{timestamp}-snapshot.json"


def write_snapshot(
    data: Any,
    destination: str | Path,
    *,
    metadata: Mapping[str, Any] | None = None,
) -> Path:
    """Write a JSON document capturing discover or metric payloads."""

    output_path = _resolve_destination(destination)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    document: dict[str, Any] = {
        "captured_at": datetime.now(UTC).isoformat(),
        "data": data,
    }
    if metadata:
        document["metadata"] = dict(metadata)

    output_path.write_text(
        json.dumps(document, indent=2, ensure_ascii=False, sort_keys=True),
        encoding="utf-8",
    )
    return output_path


def serialize_metric_snapshot(snapshot: MetricSnapshot) -> dict[str, Any]:
    """Convert a :class:`MetricSnapshot` into a JSON-friendly mapping."""

    return {
        "provider": snapshot.provider,
        "cell": snapshot.cell,
        "connection": snapshot.connection,
        "bands": snapshot.bands,
        "wan_ip": snapshot.wan_ip,
        "temperatures": {
            "antenna": snapshot.temperatures.antenna,
            "modem": snapshot.temperatures.modem,
            "power_amplifier": snapshot.temperatures.power_amplifier,
        },
        "lte": {
            "rsrp": list(snapshot.lte.rsrp),
            "sinr": list(snapshot.lte.sinr),
            "rsrq": snapshot.lte.rsrq,
            "rssi": snapshot.lte.rssi,
            "earfcn": snapshot.lte.earfcn,
            "pci": snapshot.lte.pci,
            "bandwidth": snapshot.lte.bandwidth,
        },
        "nr5g": {
            "rsrp": list(snapshot.nr5g.rsrp),
            "sinr": snapshot.nr5g.sinr,
            "arfcn": snapshot.nr5g.arfcn,
            "pci": snapshot.nr5g.pci,
            "bandwidth": snapshot.nr5g.bandwidth,
        },
        "neighbors": [
            {
                "identifier": neighbor.identifier,
                "rsrp": neighbor.rsrp,
                "rsrq": neighbor.rsrq,
            }
            for neighbor in snapshot.neighbors
        ],
        "metrics": snapshot.metric_map(),
    }


def write_metric_snapshot(
    snapshot: MetricSnapshot,
    destination: str | Path,
    *,
    metadata: Mapping[str, Any] | None = None,
) -> Path:
    """Persist a structured :class:`MetricSnapshot` for later reuse."""

    document = serialize_metric_snapshot(snapshot)
    combined_metadata: dict[str, Any] = {
        "host": snapshot.host,
        "captured_at": snapshot.timestamp.isoformat(),
    }
    if metadata:
        combined_metadata.update(metadata)

    return write_snapshot(document, destination, metadata=combined_metadata)
