"""Test fixtures helpers for modem telemetry."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

FIXTURES_ROOT = Path(__file__).resolve().parent
LATEST_FIXTURE = FIXTURES_ROOT / "modem" / "latest.json"


class FixtureError(RuntimeError):
    """Raised when a required fixture is missing or malformed."""


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


def load_latest_snapshot(path: Path | None = None) -> ModemSnapshot:
    """Load the latest modem snapshot fixture."""
    fixture_path = path or LATEST_FIXTURE
    if not fixture_path.exists():
        raise FixtureError("Modem fixture not found. Capture a payload under tests/fixtures/modem/latest.json")
    try:
        payload = json.loads(fixture_path.read_text())
    except json.JSONDecodeError as exc:
        raise FixtureError("Malformed modem fixture JSON. Validate the capture file before running tests.") from exc

    signal = payload.get("signal", {})
    return ModemSnapshot(
        timestamp=payload["timestamp"],
        rsrp=int(signal.get("rsrp", 0)),
        sinr=int(signal.get("sinr", 0)),
        provider=payload.get("provider", "unknown"),
        raw_payload=payload,
    )
