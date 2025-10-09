"""Mock MQTT broker for hello-world flows (flattened src layout)."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
try:  # Python < 3.11 fallback
    from datetime import UTC  # type: ignore
except Exception:  # pragma: no cover - compatibility path for running script on older Pythons
    UTC = timezone.utc  # type: ignore
from pathlib import Path
from typing import Any, ClassVar

from services.modem_mock import ModemSnapshot

_DEFAULT_LOG = Path("logs") / "mqtt-mock.jsonl"


@dataclass(slots=True)
class PublishRecord:
    topic: str
    payload: dict[str, Any]
    broker_host: str | None
    notes: str
    published_at: str


class MockMQTTBroker:
    """Records publishes without hitting a real broker."""

    last_record: ClassVar[PublishRecord | None] = None

    def __init__(self, device_id: str, log_path: Path | None = None) -> None:
        self.device_id = device_id
        self.log_path = Path(log_path) if log_path else _DEFAULT_LOG
        self.records: list[PublishRecord] = []

    def build_payload(self, snapshot: ModemSnapshot) -> dict[str, Any]:
        captured_at = snapshot.timestamp
        return {
            "schema_version": "0.1.0-mock",
            "device_id": self.device_id,
            "status": "mock",
            "metrics": {
                "rsrp": {"value": snapshot.rsrp, "unit": "dBm"},
                "provider": {"value": snapshot.provider, "unit": None},
                "captured_at": captured_at,
            },
            "meta": {
                "source": "mock-fixture",
                "notes": "Hello-world payload only; no live publish occurs.",
            },
        }

    def publish(
        self, snapshot: ModemSnapshot, *, topic: str, broker_host: str | None
    ) -> PublishRecord:
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


__all__ = ["MockMQTTBroker", "PublishRecord", "get_last_record"]
