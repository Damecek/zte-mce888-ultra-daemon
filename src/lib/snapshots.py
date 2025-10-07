"""Utility helpers for persisting mocked HTTP snapshots."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def save_snapshot(
    destination: Path | str,
    *,
    name: str,
    request: dict[str, Any],
    response: Any,
) -> Path:
    target_dir = Path(destination)
    target_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    target_path = target_dir / f"{timestamp}-{name}.json"
    payload = {
        "captured_at": timestamp,
        "request": request,
        "response": response,
    }
    target_path.write_text(json.dumps(payload, indent=2, sort_keys=True))
    return target_path


__all__ = ["save_snapshot"]
