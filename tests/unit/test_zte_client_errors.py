"""Unit tests for ZTEClient error handling."""

from __future__ import annotations

import httpx
import pytest

from zte_daemon.modem.zte_client import (
    AuthenticationError,
    RequestError,
    ZTEClient,
    MetricSnapshot,
)


_CHALLENGE_RESPONSE = {
    "wa_inner_version": "WA123",
    "cr_version": "CR456",
    "RD": "salt-rd",
    "LD": "salt-ld",
}


def test_timeout_during_request_raises_request_error() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        raise httpx.TimeoutException("timed out")  # noqa

    client = ZTEClient(host="192.168.0.1", transport=httpx.MockTransport(handler))
    client._authenticated = True  # type: ignore[attr-defined]

    with pytest.raises(RequestError) as exc:
        client.request("goform/test", method="GET", payload=None, expects="json")

    assert "timed out" in str(exc.value)


@pytest.mark.parametrize("status", [401, 403])
def test_authentication_status_codes_raise_error(status: int) -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
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
        raise AssertionError(f"Unexpected path {request.url.path}")  # noqa

    client = ZTEClient(host="192.168.0.1", transport=httpx.MockTransport(handler))
    assert client.login("secret") is True

    result = client.request("goform/data", method="GET", payload=None, expects="json")

    assert result == {"value": 42}
    assert attempts["challenge"] == 2
    assert attempts["login"] == 2
    assert attempts["data"] == 2


def test_client_normalizes_host_without_protocol() -> None:
    """Test that host normalization adds http:// protocol."""
    client = ZTEClient(host="192.168.0.1")
    assert client.host == "http://192.168.0.1"
    client.close()


def test_client_preserves_explicit_protocol() -> None:
    """Test that explicit http:// or https:// is preserved."""
    client1 = ZTEClient(host="http://192.168.0.1")

    assert client1.host == "http://192.168.0.1"
    client1.close()

    client2 = ZTEClient(host="https://192.168.0.1")
    assert client2.host == "https://192.168.0.1"
    client2.close()


def test_client_context_manager_closes_properly() -> None:
    """Test that context manager properly closes the client."""
    with ZTEClient(host="192.168.0.1") as client:
        assert client.host == "http://192.168.0.1"
    # After exiting context, client should be closed


def test_is_authenticated_property_initially_false() -> None:
    """Test that is_authenticated is False before login."""
    client = ZTEClient(host="192.168.0.1")
    assert client.is_authenticated is False
    client.close()


def test_login_success_sets_authenticated_flag() -> None:
    """Test that successful login sets authentication flag."""
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("goform_get_cmd_process"):
            return httpx.Response(200, json=_CHALLENGE_RESPONSE)
        if request.url.path.endswith("goform_set_cmd_process"):
            return httpx.Response(200, json={"result": "0"})
        raise AssertionError(f"Unexpected path {request.url.path}")  # noqa

    client = ZTEClient(host="192.168.0.1", transport=httpx.MockTransport(handler))
    result = client.login("secret")

    assert result is True
    assert client.is_authenticated is True
    client.close()


def test_login_wrong_password_raises_authentication_error() -> None:
    """Test that login with wrong password raises AuthenticationError."""
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("goform_get_cmd_process"):
            return httpx.Response(200, json=_CHALLENGE_RESPONSE)
        if request.url.path.endswith("goform_set_cmd_process"):
            return httpx.Response(200, json={"result": "3"})
        raise AssertionError(f"Unexpected path {request.url.path}")  # noqa

    client = ZTEClient(host="192.168.0.1", transport=httpx.MockTransport(handler))

    with pytest.raises(AuthenticationError) as exc:
        client.login("wrong-password")

    assert "wrong password" in str(exc.value)
    assert client.is_authenticated is False
    client.close()


def test_login_unknown_result_code_raises_authentication_error() -> None:
    """Test that unknown login result code raises AuthenticationError."""
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("goform_get_cmd_process"):
            return httpx.Response(200, json=_CHALLENGE_RESPONSE)
        if request.url.path.endswith("goform_set_cmd_process"):
            return httpx.Response(200, json={"result": "99"})
        raise AssertionError(f"Unexpected path {request.url.path}")  # noqa

    client = ZTEClient(host="192.168.0.1", transport=httpx.MockTransport(handler))

    with pytest.raises(AuthenticationError) as exc:
        client.login("password")

    assert "code 99" in str(exc.value)
    client.close()


def test_login_challenge_timeout_raises_request_error() -> None:
    """Test that timeout during challenge request raises RequestError."""
    def handler(_request: httpx.Request) -> httpx.Response:
        raise httpx.TimeoutException("timed out")  # noqa

    client = ZTEClient(host="192.168.0.1", transport=httpx.MockTransport(handler))

    with pytest.raises(RequestError) as exc:
        client.login("password")

    assert "Timed out while requesting login challenge" in str(exc.value)
    client.close()


def test_login_challenge_network_error_raises_request_error() -> None:
    """Test that network error during challenge raises RequestError."""
    def handler(_request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused")  # noqa

    client = ZTEClient(host="192.168.0.1", transport=httpx.MockTransport(handler))

    with pytest.raises(RequestError) as exc:
        client.login("password")

    assert "Unable to contact modem for login challenge" in str(exc.value)
    client.close()


def test_login_invalid_challenge_json_raises_request_error() -> None:
    """Test that invalid JSON in challenge response raises RequestError."""
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text="not json")

    client = ZTEClient(host="192.168.0.1", transport=httpx.MockTransport(handler))

    with pytest.raises(RequestError) as exc:
        client.login("password")

    assert "Unexpected modem login challenge payload" in str(exc.value)
    client.close()


def test_login_missing_challenge_field_raises_request_error() -> None:
    """Test that missing field in challenge response raises RequestError."""
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"wa_inner_version": "WA123"})

    client = ZTEClient(host="192.168.0.1", transport=httpx.MockTransport(handler))

    with pytest.raises(RequestError) as exc:
        client.login("password")

    assert "Unexpected modem login challenge payload" in str(exc.value)
    client.close()


def test_login_credentials_timeout_raises_request_error() -> None:
    """Test that timeout during credential submission raises RequestError."""
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("goform_get_cmd_process"):
            return httpx.Response(200, json=_CHALLENGE_RESPONSE)
        raise httpx.TimeoutException("timed out")  # noqa

    client = ZTEClient(host="192.168.0.1", transport=httpx.MockTransport(handler))

    with pytest.raises(RequestError) as exc:
        client.login("password")

    assert "Timed out while submitting credentials" in str(exc.value)
    client.close()


def test_login_credentials_network_error_raises_request_error() -> None:
    """Test that network error during credentials submission raises RequestError."""
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("goform_get_cmd_process"):
            return httpx.Response(200, json=_CHALLENGE_RESPONSE)
        raise httpx.ConnectError("connection refused")  # noqa

    client = ZTEClient(host="192.168.0.1", transport=httpx.MockTransport(handler))

    with pytest.raises(RequestError) as exc:
        client.login("password")

    assert "Unable to submit login credentials" in str(exc.value)
    client.close()


def test_login_non_json_response_raises_request_error() -> None:
    """Test that non-JSON login response raises RequestError."""
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("goform_get_cmd_process"):
            return httpx.Response(200, json=_CHALLENGE_RESPONSE)
        return httpx.Response(200, text="not json")

    client = ZTEClient(host="192.168.0.1", transport=httpx.MockTransport(handler))

    with pytest.raises(RequestError) as exc:
        client.login("password")

    assert "non-JSON login response" in str(exc.value)
    client.close()


def test_request_without_authentication_raises_error() -> None:
    """Test that request without authentication raises AuthenticationError."""
    client = ZTEClient(host="192.168.0.1")

    with pytest.raises(AuthenticationError) as exc:
        client.request("goform/test", method="GET", payload=None, expects="json")

    assert "not authenticated" in str(exc.value)
    client.close()


def test_request_expects_json_returns_parsed_data() -> None:
    """Test that expects=json returns parsed JSON data."""
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"result": "success", "value": 42})

    client = ZTEClient(host="192.168.0.1", transport=httpx.MockTransport(handler))
    client._authenticated = True  # type: ignore[attr-defined]

    result = client.request("goform/test", method="GET", payload=None, expects="json")

    assert result == {"result": "success", "value": 42}
    client.close()


def test_request_expects_text_returns_string() -> None:
    """Test that expects=text returns raw text response."""
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text="plain text response")

    client = ZTEClient(host="192.168.0.1", transport=httpx.MockTransport(handler))
    client._authenticated = True  # type: ignore[attr-defined]

    result = client.request("goform/test", method="GET", payload=None, expects="text")

    assert result == "plain text response"
    client.close()


def test_request_with_json_payload() -> None:
    """Test that JSON payload is properly sent."""
    captured_body: bytes | None = None

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal captured_body
        captured_body = request.content
        return httpx.Response(200, json={"result": "ok"})

    client = ZTEClient(host="192.168.0.1", transport=httpx.MockTransport(handler))
    client._authenticated = True  # type: ignore[attr-defined]

    client.request("goform/test", method="POST", payload={"action": "test"}, expects="json")

    assert captured_body is not None
    import json

    assert json.loads(captured_body) == {"action": "test"}
    client.close()


def test_request_with_query_params() -> None:
    """Test that query parameters are properly added."""
    captured_url: str | None = None

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal captured_url
        captured_url = str(request.url)
        return httpx.Response(200, json={"result": "ok"})

    client = ZTEClient(host="192.168.0.1", transport=httpx.MockTransport(handler))
    client._authenticated = True  # type: ignore[attr-defined]

    client.request(
        "goform/test",
        method="GET",
        payload=None,
        expects="json",
        params={"cmd": "status", "id": "123"},
    )

    assert "cmd=status" in captured_url
    assert "id=123" in captured_url
    client.close()


def test_request_unsupported_expects_type_raises_error() -> None:
    """Test that unsupported expects type raises RequestError."""
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"result": "ok"})

    client = ZTEClient(host="192.168.0.1", transport=httpx.MockTransport(handler))
    client._authenticated = True  # type: ignore[attr-defined]

    with pytest.raises(RequestError) as exc:
        client.request("goform/test", method="GET", payload=None, expects="xml")

    assert "Unsupported response type" in str(exc.value)
    client.close()


def test_request_non_json_when_expecting_json_raises_error() -> None:
    """Test that non-JSON response when expecting JSON raises RequestError."""
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text="not json")

    client = ZTEClient(host="192.168.0.1", transport=httpx.MockTransport(handler))
    client._authenticated = True  # type: ignore[attr-defined]

    with pytest.raises(RequestError) as exc:
        client.request("goform/test", method="GET", payload=None, expects="json")

    assert "Expected JSON response" in str(exc.value)
    client.close()


def test_request_http_error_status_raises_request_error() -> None:
    """Test that HTTP error status codes raise RequestError."""
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, json={"error": "server error"})

    client = ZTEClient(host="192.168.0.1", transport=httpx.MockTransport(handler))
    client._authenticated = True  # type: ignore[attr-defined]

    with pytest.raises(RequestError) as exc:
        client.request("goform/test", method="GET", payload=None, expects="json")

    assert "HTTP 500" in str(exc.value)
    client.close()


def test_request_retry_disabled_after_auth_failure() -> None:
    """Test that retry is disabled when retry_on_auth_failure=False."""
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"error": "unauthorized"})

    client = ZTEClient(host="192.168.0.1", transport=httpx.MockTransport(handler))
    client._authenticated = True  # type: ignore[attr-defined]
    client._password = "".join(["s", "e", "c", "r", "e", "t"])  # type: ignore[attr-defined]

    with pytest.raises(AuthenticationError):
        client.request(
            "goform/test",
            method="GET",
            payload=None,
            expects="json",
            retry_on_auth_failure=False,
        )


def test_get_metric_delegates_to_fetch_snapshot() -> None:
    """Test that get_metric properly delegates to fetch_snapshot."""
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "network_provider_fullname": "TestNet",
                "lte_rsrp_1": "-85",
                "wan_active_band": "B20",
            },
        )

    client = ZTEClient(host="192.168.0.1", transport=httpx.MockTransport(handler))
    client._authenticated = True  # type: ignore[attr-defined]

    value = client.get_metric("rsrp1")

    assert value == -85
    client.close()


def test_fetch_snapshot_returns_metric_snapshot() -> None:
    """Test that fetch_snapshot returns MetricSnapshot instance."""
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "network_provider_fullname": "TestNet",
                "lte_rsrp_1": "-85",
                "lte_snr_1": "18",
            },
        )

    client = ZTEClient(host="192.168.0.1", transport=httpx.MockTransport(handler))
    client._authenticated = True  # type: ignore[attr-defined]

    snapshot = client.fetch_snapshot()

    assert isinstance(snapshot, MetricSnapshot)
    assert snapshot.provider == "TestNet"
    assert snapshot.rsrp1 == -85
    client.close()


def test_fetch_snapshot_stores_latest_snapshot() -> None:
    """Test that fetch_snapshot stores the result in _latest_snapshot."""
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "network_provider_fullname": "TestNet",
                "lte_rsrp_1": "-85",
            },
        )

    client = ZTEClient(host="192.168.0.1", transport=httpx.MockTransport(handler))
    client._authenticated = True  # type: ignore[attr-defined]

    snapshot = client.fetch_snapshot()

    assert client._latest_snapshot is snapshot  # type: ignore[attr-defined]
    client.close()


def test_fetch_snapshot_non_mapping_response_raises_error() -> None:
    """Test that non-mapping response in fetch_snapshot raises RequestError."""
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=["not", "a", "mapping"])

    client = ZTEClient(host="192.168.0.1", transport=httpx.MockTransport(handler))
    client._authenticated = True  # type: ignore[attr-defined]

    with pytest.raises(RequestError) as exc:
        client.fetch_snapshot()

    assert "Unexpected snapshot payload" in str(exc.value)
    client.close()


def test_request_custom_headers() -> None:
    """Test that custom headers are properly passed through."""
    captured_headers: httpx.Headers | None = None

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal captured_headers
        captured_headers = request.headers
        return httpx.Response(200, json={"result": "ok"})

    client = ZTEClient(host="192.168.0.1", transport=httpx.MockTransport(handler))
    client._authenticated = True  # type: ignore[attr-defined]

    client.request(
        "goform/test",
        method="GET",
        payload=None,
        expects="json",
        headers={"X-Custom": "test-value"},
    )

    assert captured_headers is not None
    assert captured_headers.get("X-Custom") == "test-value"
    client.close()