"""Utilities for persisting modem snapshots and discover payloads."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Mapping

from zte_daemon.modem.metrics import MetricSnapshot

__all__ = ["write_snapshot", "serialize_metric_snapshot", "write_metric_snapshot"]


def _resolve_destination(destination: str | Path) -> Path:
    """
    Resolve a destination into a filesystem path for writing a snapshot.
    
    If `destination` denotes a file (has a suffix), return that path unchanged.
    If it denotes a directory (no suffix), return a new Path inside that directory
    with a UTC timestamped filename of the form `<YYYYMMDDTHHMMSSZ>-snapshot.json`.
    
    Parameters:
        destination (str | Path): Target file path or directory.
    
    Returns:
        Path: The resolved file path where the snapshot should be written.
    """
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
    """
    Persist a JSON snapshot containing the given payload and optional metadata to the filesystem.
    
    Writes a JSON document with keys "captured_at" (current UTC time in ISO format) and "data" (the provided payload). If metadata is provided, it is copied into the document under the "metadata" key. If the destination path has no file suffix, a timestamped filename is appended; parent directories are created if necessary.
    
    Parameters:
        data (Any): The payload to store under the "data" key of the JSON document.
        destination (str | Path): Target file path or directory. If a directory or a path without a suffix is given, a timestamped filename is appended.
        metadata (Mapping[str, Any] | None): Optional mapping to include under the "metadata" key.
    
    Returns:
        Path: The filesystem path where the JSON snapshot was written.
    """

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
    """
    Serialize a MetricSnapshot into a JSON-serializable mapping.
    
    Parameters:
        snapshot (MetricSnapshot): The metric snapshot to serialize.
    
    Returns:
        dict[str, Any]: A mapping containing snapshot fields suitable for JSON encoding with keys:
            - provider, cell, connection, bands, wan_ip
            - temperatures: dict with `antenna`, `modem`, `power_amplifier`
            - lte: dict with `rsrp` (list), `sinr` (list), `rsrq`, `rssi`, `earfcn`, `pci`, `bandwidth`
            - nr5g: dict with `rsrp` (list), `sinr`, `arfcn`, `pci`, `bandwidth`
            - neighbors: list of dicts each with `identifier`, `rsrp`, `rsrq`
            - metrics: mapping produced by the snapshot's metric_map()
    """

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
    """
    Write a serialized representation of a MetricSnapshot to the given destination path.
    
    Parameters:
        snapshot (MetricSnapshot): Snapshot to serialize and persist.
        destination (str | Path): File path or directory where the JSON file will be written. If a directory is provided, a timestamped filename will be appended.
        metadata (Mapping[str, Any] | None): Additional metadata to merge into the stored metadata; merged with `host` and `captured_at` derived from the snapshot.
    
    Returns:
        path (Path): Path to the written JSON file.
    """

    document = serialize_metric_snapshot(snapshot)
    combined_metadata: dict[str, Any] = {
        "host": snapshot.host,
        "captured_at": snapshot.timestamp.isoformat(),
    }
    if metadata:
        combined_metadata.update(metadata)

    return write_snapshot(document, destination, metadata=combined_metadata)