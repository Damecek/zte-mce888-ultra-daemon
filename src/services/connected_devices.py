from __future__ import annotations

import json
from typing import Any

from lib.value_coerce import coerce_number_like as _coerce


def _clean_string(value: Any) -> str | None:
    """Trim string-like values; return None when the input is None."""
    if value is None:
        return None
    if isinstance(value, str):
        return value.strip()
    return str(value)


def parse_connected_devices(raw: Any) -> list[dict[str, Any]]:
    """
    Normalize the ``lan_station_list`` payload into a list of device mappings.

    The modem typically responds with ``{"lan_station_list": [{...}]}``, where
    each entry contains string fields. Numeric string fields are coerced using
    ``coerce_number_like`` and string fields are trimmed.
    """
    if not raw:
        return []

    data: Any = raw
    if isinstance(raw, str):
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            return []

    if not isinstance(data, list):
        return []

    devices: list[dict[str, Any]] = []
    for entry in data:
        if not isinstance(entry, dict):
            continue
        devices.append({
            "hostname": _clean_string(entry.get("hostname")),
            "ip": _clean_string(entry.get("ip_addr")),
            "mac": _clean_string(entry.get("mac_addr")),
            "connect_time": _coerce(entry.get("connect_time")),
            "mac_bind_flag": _coerce(entry.get("mac_bind_flag")),
        })
    return devices


__all__ = ["parse_connected_devices"]
