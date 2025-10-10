from __future__ import annotations

import json
from pathlib import Path

from lib.snapshots import save_snapshot


def test_save_snapshot_creates_timestamped_file(tmp_path: Path) -> None:
    dest = tmp_path / "docs" / "discover"
    created = save_snapshot(
        dest,
        name="lan_station_list",
        request={"host": "h", "path": "/goform/p", "method": "GET", "payload": None},
        response={"stations": []},
    )
    # File exists and is under destination directory
    assert created.exists()
    assert created.parent == dest
    assert created.name.endswith("-lan_station_list.json")

    # Payload structure contains captured_at, request, response
    data = json.loads(created.read_text())
    assert "captured_at" in data and isinstance(data["captured_at"], str)
    assert data["request"]["method"] == "GET"
    assert data["response"] == {"stations": []}
