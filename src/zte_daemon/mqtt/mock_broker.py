"""Mock MQTT broker for hello-world flows."""
from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, ClassVar, Dict, List, Optional, Protocol, runtime_checkable

from zte_daemon.modem.metrics import MetricSnapshot

_DEFAULT_LOG = Path("logs") / "mqtt-mock.jsonl"


@dataclass(slots=True)
class PublishRecord:
    topic: str
    payload: Dict[str, Any]
    broker_host: Optional[str]
    notes: str
    published_at: str


@runtime_checkable
class SnapshotProtocol(Protocol):
    timestamp: Any
    provider: Any


class MockMQTTBroker:
    """Records publishes without hitting a real broker."""

    last_record: ClassVar[PublishRecord | None] = None

    def __init__(self, device_id: str, log_path: Path | None = None) -> None:
        """
        Initialize a MockMQTTBroker for recording published payloads to a log file.
        
        Parameters:
            device_id (str): Identifier for the device whose publishes will be recorded.
            log_path (Path | None): Path to the log file where records will be appended; if None, uses the module default log path.
        """
        self.device_id = device_id
        self.log_path = Path(log_path) if log_path else _DEFAULT_LOG
        self.records: List[PublishRecord] = []

    def _extract_metrics(self, snapshot: SnapshotProtocol) -> tuple[Any, Any, str]:
        """
        Extracts provider, RSRP value, and capture timestamp from a snapshot-like object.
        
        If the snapshot is a MetricSnapshot, the timestamp is returned as an ISO-formatted string and `rsrp1` and `provider` are used. For other snapshot shapes, the function returns `snapshot.timestamp` as-is, prefers `rsrp1` if present otherwise falls back to `rsrp`, and reads `provider` if available.
        
        Parameters:
            snapshot (SnapshotProtocol): Snapshot-like object with a `timestamp` and optional `rsrp1`, `rsrp`, and `provider` attributes.
        
        Returns:
            tuple: A 3-tuple (provider, rsrp_value, captured_at) where:
                - provider: the snapshot's provider value or None if unavailable
                - rsrp_value: the preferred RSRP value (`rsrp1` or `rsrp`) or None
                - captured_at: ISO-formatted timestamp for MetricSnapshot, otherwise the snapshot's `timestamp` value
        """
        if isinstance(snapshot, MetricSnapshot):
            captured_at = snapshot.timestamp.isoformat()
            rsrp_value = snapshot.rsrp1
            provider = snapshot.provider
        else:
            captured_at = snapshot.timestamp
            if hasattr(snapshot, "rsrp1"):
                rsrp_value = getattr(snapshot, "rsrp1")
            else:
                rsrp_value = getattr(snapshot, "rsrp", None)
            provider = getattr(snapshot, "provider", None)
        return provider, rsrp_value, captured_at

    def build_payload(self, snapshot: SnapshotProtocol) -> Dict[str, Any]:
        """
        Builds the MQTT mock payload for a given snapshot.
        
        Parameters:
            snapshot (SnapshotProtocol): Snapshot-like object from which metrics (provider, RSRP, timestamp) are extracted.
        
        Returns:
            Dict[str, Any]: A serializable payload containing:
                - schema_version: payload schema identifier
                - device_id: this broker's device identifier
                - status: "mock"
                - metrics: mapping with `rsrp` (value in dBm), `provider` (value), and `captured_at` (ISO timestamp)
                - meta: source and notes indicating this is a mock payload
        """
        provider, rsrp_value, captured_at = self._extract_metrics(snapshot)
        return {
            "schema_version": "0.1.0-mock",
            "device_id": self.device_id,
            "status": "mock",
            "metrics": {
                "rsrp": {"value": rsrp_value, "unit": "dBm"},
                "provider": {"value": provider, "unit": None},
                "captured_at": captured_at,
            },
            "meta": {
                "source": "mock-fixture",
                "notes": "Hello-world payload only; no live publish occurs.",
            },
        }

    def publish(
        self, snapshot: SnapshotProtocol, *, topic: str, broker_host: str | None
    ) -> PublishRecord:
        """
        Record a mock MQTT publish for the given snapshot and persist it to the mock log.
        
        Parameters:
            snapshot (SnapshotProtocol): Snapshot-like object used to build the recorded payload (must provide timestamp and provider; may include `rsrp1` or `rsrp`).
            topic (str): MQTT topic associated with the recorded publish.
            broker_host (str | None): Optional broker host to annotate the record; when None, a default-note is used.
        
        Returns:
            PublishRecord: The created publish record including topic, payload, broker_host, notes, and ISO-formatted publication time.
        
        Side effects:
            - Appends the record to this instance's records list.
            - Updates MockMQTTBroker.last_record to the created record.
            - Appends the record as a JSON line to the configured log file.
        """
        payload = self.build_payload(snapshot)
        note = (
            "Recorded publish to mock broker defaults"
            if not broker_host
            else f"Recorded publish for broker {broker_host}"
        )
        record = PublishRecord(
            topic=topic,
            payload=payload,
            broker_host=broker_host,
            notes=note,
            published_at=datetime.now(UTC).isoformat(),
        )
        self.records.append(record)
        MockMQTTBroker.last_record = record
        self._write_record(record)
        return record

    def _write_record(self, record: PublishRecord) -> None:
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        with self.log_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(asdict(record), ensure_ascii=False) + "\n")


def get_last_record() -> PublishRecord | None:
    """Return the most recent publish record for test inspection."""
    return MockMQTTBroker.last_record