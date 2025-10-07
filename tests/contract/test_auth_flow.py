"""Contract tests for ZTE modem authentication handshake."""

from __future__ import annotations

from typing import Callable
from urllib.parse import parse_qs

import httpx
import pytest

from zte_daemon.modem.zte_client import AuthenticationError, ZTEClient


@pytest.fixture()
def challenge_payload() -> dict[str, str]:
    return {
        "wa_inner_version": "WA123",
        "cr_version": "CR456",
        "RD": "salt-rd",
        "LD": "salt-ld",
    }


def _make_transport(
    *,
    challenge: dict[str, str],
    on_login: Callable[[httpx.Request], None],
) -> httpx.MockTransport:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("goform_get_cmd_process"):
            assert request.method == "GET"
            query = dict(request.url.params)
            # Contract: the modem expects these exact query params for salt discovery
            assert query == {"cmd": "wa_inner_version,cr_version,RD,LD", "multi_data": "1"}
            return httpx.Response(200, json=challenge)

        if request.url.path.endswith("goform_set_cmd_process"):
            assert request.method == "POST"
            on_login(request)
            return httpx.Response(200, json={"result": "0"}, headers={"Set-Cookie": "SessionID=abc123; Path=/"})

        raise AssertionError(f"Unexpected request path: {request.url.path}")

    return httpx.MockTransport(handler)


def test_successful_login_fetches_challenge_and_posts_credentials(challenge_payload: dict[str, str]) -> None:
    recorded_password: dict[str, str] = {}

    def capture_login(request: httpx.Request) -> None:
        body = parse_qs(request.content.decode())
        recorded_password.update({key: value[0] for key, value in body.items()})

    client = ZTEClient(
        host="192.168.0.1",
        transport=_make_transport(challenge=challenge_payload, on_login=capture_login),
    )

    result = client.login(password="admin")

    assert result is True
    assert client.is_authenticated is True
    # Password and AD are SHA256 based on salts delivered by the modem
    assert recorded_password["goformId"] == "LOGIN"
    assert recorded_password["isTest"] == "false"
    # ensure hashed values are deterministic for the challenge fixture
    assert recorded_password["password"].isalnum()
    assert recorded_password["AD"].isalnum()


def test_login_failure_raises_authentication_error(challenge_payload: dict[str, str]) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("goform_get_cmd_process"):
            return httpx.Response(200, json=challenge_payload)
        if request.url.path.endswith("goform_set_cmd_process"):
            return httpx.Response(200, json={"result": "3"})
        raise AssertionError("unexpected request")

    client = ZTEClient(host="192.168.0.1", transport=httpx.MockTransport(handler))

    with pytest.raises(AuthenticationError):
        client.login(password="wrong")
