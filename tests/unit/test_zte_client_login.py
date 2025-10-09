from __future__ import annotations

import hashlib

import httpx
import pytest

from services import zte_client


def test_hash_helpers_produce_expected_hex() -> None:
    # Validate against hashlib to avoid hardcoding values
    assert zte_client.sha256_hex("pw") == hashlib.sha256(b"pw").hexdigest().upper()
    assert zte_client.md5_hex("pw") == hashlib.md5(b"pw").hexdigest().upper()


def test_normalize_host_adds_scheme() -> None:
    client = zte_client.ZTEClient("192.168.0.1", transport=httpx.MockTransport(lambda r: httpx.Response(200)))
    try:
        assert client.base_url == "http://192.168.0.1"
    finally:
        client.close()


def _auth_flow_transport(sequence: list[str]):
    """Return a transport handler that simulates handshake, login and data fetch.

    sequence: controls responses for data fetch path: items are "401" or "200" in order.
    """

    # Simple state container in closure
    counters = {"data_calls": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        # Handshake GET
        if request.url.path.endswith("/goform/goform_get_cmd_process") and request.method == "GET":
            # Handshake: provide required keys; include MC888 to select sha256
            payload = {"wa_inner_version": "MC888_V1", "cr_version": "X", "RD": "r", "LD": "l"}
            return httpx.Response(200, json=payload)
        # Login POST
        if request.url.path.endswith("/goform/goform_set_cmd_process") and request.method == "POST":
            # Login: set cookie to mark session
            headers = {"set-cookie": "SESSIONID=f00d; Path=/"}
            return httpx.Response(200, headers=headers)

        # Data fetch path: first response(s) as per sequence, then 200 JSON
        if request.method in {"GET", "POST"}:
            idx = counters["data_calls"]
            if idx < len(sequence) and sequence[idx] == "401":
                counters["data_calls"] += 1
                return httpx.Response(401, json={"error": "auth"})
            counters["data_calls"] += 1
            return httpx.Response(200, json={"ok": True})

        return httpx.Response(404)

    return handler


def test_login_succeeds_and_request_returns_json() -> None:
    transport = httpx.MockTransport(_auth_flow_transport(sequence=[]))
    client = zte_client.ZTEClient("http://example", transport=transport)
    try:
        client.login("pw")
        assert client._session.authenticated is True
        assert client._session.cookie and client._session.cookie.startswith("SESSIONID=")
        data = client.request("/data", method="GET")
        assert data == {"ok": True}
    finally:
        client.close()


def test_request_reauthenticates_on_401_and_retries() -> None:
    # First data call returns 401, then 200; client should re-login and retry once
    transport = httpx.MockTransport(_auth_flow_transport(sequence=["401"]))
    client = zte_client.ZTEClient("http://example", transport=transport)
    try:
        client.login("pw")
        data = client.request("/data", method="GET")
        assert data == {"ok": True}
    finally:
        client.close()


def test_login_without_set_cookie_raises_auth_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("goform_get_cmd_process"):
            return httpx.Response(200, json={"wa_inner_version": "X", "cr_version": "Y", "RD": "r", "LD": "l"})
        if request.url.path.endswith("goform_set_cmd_process"):
            # No set-cookie header -> should raise AuthenticationError
            return httpx.Response(200)
        return httpx.Response(404)

    client = zte_client.ZTEClient("http://example", transport=httpx.MockTransport(handler))
    try:
        with pytest.raises(zte_client.AuthenticationError):
            client.login("pw")
    finally:
        client.close()
