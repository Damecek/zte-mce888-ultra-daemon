"""Mock modem client that loads captured fixtures (flattened src layout)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

_DEFAULT_FIXTURE = (
    Path(__file__).resolve().parents[2] / "tests" / "fixtures" / "modem" / "latest.json"
)


class ModemFixtureError(RuntimeError):
    """Raised when modem fixtures are unavailable or malformed."""


def _to_datetime(value: str) -> datetime:
    if value.endswith("Z"):
        value = value.replace("Z", "+00:00")
    return datetime.fromisoformat(value)


@dataclass(slots=True)
class ModemSnapshot:
    timestamp: str
    rsrp: int
    sinr: int
    provider: str
    raw_payload: dict[str, Any]

    @property
    def metric_map(self) -> dict[str, Any]:
        return {
            "RSRP": self.rsrp,
            "Provider": self.provider,
        }


class MockModemClient:
    """Loads modem telemetry from fixtures for the hello-world CLI."""

    def __init__(self, fixture_path: Path | None = None) -> None:
        self._fixture_path = Path(fixture_path) if fixture_path else _DEFAULT_FIXTURE
        self._snapshot: ModemSnapshot | None = None
        self._last_timestamp: datetime | None = None

    def load_snapshot(self, path: Path | None = None) -> ModemSnapshot:
        fixture_path = Path(path) if path else self._fixture_path
        if not fixture_path.exists():
            raise ModemFixtureError(
                "Modem fixture not found. Capture a payload under tests/fixtures/modem/latest.json"
            )
        try:
            payload = json.loads(fixture_path.read_text())
        except json.JSONDecodeError as exc:  # pragma: no cover - extremely unlikely
            raise ModemFixtureError(
                "Malformed modem fixture JSON. Validate the capture file before running the CLI."
            ) from exc

        timestamp = payload["timestamp"]
        current_dt = _to_datetime(timestamp)
        if self._last_timestamp and current_dt <= self._last_timestamp:
            raise RuntimeError(
                "Modem snapshot timestamp must increase monotonically between captures."
            )
        signal = payload.get("signal", {})
        snapshot = ModemSnapshot(
            timestamp=timestamp,
            rsrp=int(signal.get("rsrp", 0)),
            sinr=int(signal.get("sinr", 0)),
            provider=payload.get("provider", "unknown"),
            raw_payload=payload,
        )
        self._snapshot = snapshot
        self._last_timestamp = current_dt
        return snapshot

    def read_metric(self, metric: str) -> Any:
        snapshot = self._snapshot or self.load_snapshot()
        metric_map = snapshot.metric_map
        if metric not in metric_map:
            raise KeyError(metric)
        return metric_map[metric]

    @property
    def snapshot(self) -> ModemSnapshot:
        if not self._snapshot:
            return self.load_snapshot()
        return self._snapshot


__all__ = [
    "MockModemClient",
    "ModemSnapshot",
    "ModemFixtureError",
]
