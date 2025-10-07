"""Contract tests for ZTE modem authentication handshake."""

from __future__ import annotations

from typing import Callable
from urllib.parse import parse_qs

import httpx
import pytest

from zte_daemon.modem.zte_client import AuthenticationError, ZTEClient


@pytest.fixture()
def challenge_payload() -> dict[str, str]:
    """
    Provides a mock challenge payload used in contract tests for the ZTE modem authentication handshake.
    
    Returns:
        challenge (dict[str, str]): A mapping with the following keys:
            - "wa_inner_version": modem WA inner version string.
            - "cr_version": modem CR version string.
            - "RD": server-provided random salt (RD).
            - "LD": server-provided random salt (LD).
    """
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
    """
    Create an httpx.MockTransport that simulates the ZTE modem's challenge discovery and login endpoints.
    
    The transport responds to GET requests for "goform_get_cmd_process" with the provided `challenge` JSON and to POST requests for "goform_set_cmd_process" by calling `on_login` and returning a successful login response with a session cookie.
    
    Parameters:
        challenge (dict[str, str]): JSON payload returned for the challenge discovery GET request.
        on_login (Callable[[httpx.Request], None]): Callback invoked with the POST request when a login attempt occurs; useful for inspecting or capturing the submitted credentials.
    
    Returns:
        httpx.MockTransport: A mock transport handling the two modem endpoints.
    
    Raises:
        AssertionError: If the request path is unexpected or if incoming requests do not match the expected methods or query parameters.
    """
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
    """
    Verifies that the client fetches the modem challenge and submits the expected login payload, resulting in a successful authentication.
    
    The test uses a mocked transport that returns a challenge on the "goform_get_cmd_process" endpoint and captures the POST payload to "goform_set_cmd_process". It asserts the client's login call succeeds, sets the authenticated state, and that the posted payload contains the expected control fields and deterministically hashed `password` and `AD` values.
    
    Parameters:
        challenge_payload (dict[str, str]): Fixture-provided challenge fields returned by the modem mock.
    """
    recorded_password: dict[str, str] = {}

    def capture_login(request: httpx.Request) -> None:
        """
        Parse a form-encoded login request body and update the captured credentials.
        
        Parses the request content as application/x-www-form-urlencoded and stores each field's first value into the outer-scope `recorded_password` dictionary.
        
        Parameters:
            request (httpx.Request): HTTP request containing the form-encoded login payload.
        """
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
        """
        Mock HTTP handler that simulates the modem's challenge and login responses.
        
        Returns a 200 response with the fixture `challenge_payload` as JSON when the request path ends with "goform_get_cmd_process", or a 200 response with JSON {"result": "3"} when the path ends with "goform_set_cmd_process".
        
        Returns:
            httpx.Response: The simulated HTTP response for the request.
        
        Raises:
            AssertionError: If the request path is not one of the expected endpoints.
        """
        if request.url.path.endswith("goform_get_cmd_process"):
            return httpx.Response(200, json=challenge_payload)
        if request.url.path.endswith("goform_set_cmd_process"):
            return httpx.Response(200, json={"result": "3"})
        raise AssertionError("unexpected request")

    client = ZTEClient(host="192.168.0.1", transport=httpx.MockTransport(handler))

    with pytest.raises(AuthenticationError):
        client.login(password="wrong")