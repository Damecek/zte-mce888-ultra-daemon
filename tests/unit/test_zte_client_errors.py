"""Unit tests for ZTEClient error handling."""

from __future__ import annotations

import httpx
import pytest

from zte_daemon.modem.zte_client import AuthenticationError, RequestError, ZTEClient


_CHALLENGE_RESPONSE = {
    "wa_inner_version": "WA123",
    "cr_version": "CR456",
    "RD": "salt-rd",
    "LD": "salt-ld",
}


def test_timeout_during_request_raises_request_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.TimeoutException("timed out")

    client = ZTEClient(host="192.168.0.1", transport=httpx.MockTransport(handler))
    client._authenticated = True  # type: ignore[attr-defined]

    with pytest.raises(RequestError) as exc:
        client.request("goform/test", method="GET", payload=None, expects="json")

    assert "timed out" in str(exc.value)


@pytest.mark.parametrize("status", [401, 403])
def test_authentication_status_codes_raise_error(status: int) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(status, json={"error": "nope"})

    client = ZTEClient(host="192.168.0.1", transport=httpx.MockTransport(handler))
    client._authenticated = True  # type: ignore[attr-defined]

    with pytest.raises(AuthenticationError):
        client.request("goform/test", method="GET", payload=None, expects="json")


def test_request_retries_after_session_expiry() -> None:
    attempts: dict[str, int] = {"challenge": 0, "login": 0, "data": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("goform_get_cmd_process"):
            attempts["challenge"] += 1
            return httpx.Response(200, json=_CHALLENGE_RESPONSE)
        if request.url.path.endswith("goform_set_cmd_process"):
            attempts["login"] += 1
            return httpx.Response(200, json={"result": "0"})
        if request.url.path.endswith("goform/data"):
            attempts["data"] += 1
            if attempts["data"] == 1:
                return httpx.Response(401, json={"error": "expired"})
            return httpx.Response(200, json={"value": 42})
        raise AssertionError(f"Unexpected path {request.url.path}")

    client = ZTEClient(host="192.168.0.1", transport=httpx.MockTransport(handler))
    assert client.login("secret") is True

    result = client.request("goform/data", method="GET", payload=None, expects="json")

    assert result == {"value": 42}
    assert attempts["challenge"] == 2
    assert attempts["login"] == 2
    assert attempts["data"] == 2
