from __future__ import annotations

import json

from services.connected_devices import parse_connected_devices


def test_parse_connected_devices_trims_and_coerces() -> None:
    raw = [
        {
            "hostname": " Laptop ",
            "ip_addr": "192.0.2.30 ",
            "mac_addr": " 02:00:00:00:00:30 ",
            "connect_time": "123",
            "mac_bind_flag": "1",
        }
    ]

    result = parse_connected_devices(raw)

    assert result == [
        {
            "hostname": "Laptop",
            "ip": "192.0.2.30",
            "mac": "02:00:00:00:00:30",
            "connect_time": 123,
            "mac_bind_flag": 1,
        }
    ]


def test_parse_connected_devices_accepts_string_payload() -> None:
    payload = json.dumps([
        {
            "hostname": "Phone",
            "ip_addr": "192.0.2.40",
            "mac_addr": "02:00:00:00:00:40",
            "connect_time": "42",
            "mac_bind_flag": "2",
        }
    ])

    result = parse_connected_devices(payload)

    assert result[0]["hostname"] == "Phone"
    assert result[0]["connect_time"] == 42


def test_parse_connected_devices_handles_invalid_payload() -> None:
    assert parse_connected_devices(None) == []
    assert parse_connected_devices("{}") == []
    assert parse_connected_devices([None, "garbage"]) == []
