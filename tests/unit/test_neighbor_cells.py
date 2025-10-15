from __future__ import annotations

from services.neighbor_cells import parse_neighbors


def test_parse_neighbors_parses_and_coerces() -> None:
    raw = "1800,123,5,-95,-60;3500,456,8,-105,-70"
    out = parse_neighbors(raw)
    assert len(out) == 2
    assert out[0]["id"] == 123
    assert out[0]["rsrp"] == -95
    assert out[1]["freq"] == 3500


def test_parse_neighbors_ignores_malformed_and_empty() -> None:
    raw = ";;2000,12,,-100,-60;badentry;"
    out = parse_neighbors(raw)
    # One valid after malformed entries
    assert len(out) == 1
    assert out[0]["id"] == 12
