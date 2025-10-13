from __future__ import annotations

from typing import Any

from lib.value_coerce import coerce_number_like as _coerce


def parse_neighbors(raw: Any) -> list[dict[str, Any]]:
    """
    Parse ngbr_cell_info payload ("freq,pci,rsrq,rsrp,rssi;...") into a list of dicts.

    Unknown or malformed entries are ignored. Numeric fields are coerced to int/float when possible.
    Returns an empty list for falsy inputs.
    """
    if not raw:
        return []
    items: list[dict[str, Any]] = []
    for cell in str(raw).split(";"):
        if not cell:
            continue
        parts = cell.split(",")
        if len(parts) < 5:
            continue
        freq, pci, rsrq, rsrp, rssi = parts[:5]
        items.append({
            "id": _coerce(pci),
            "rsrp": _coerce(rsrp),
            "rsrq": _coerce(rsrq),
            "freq": _coerce(freq),
            "rssi": _coerce(rssi),
        })
    return items


__all__ = ["parse_neighbors"]
