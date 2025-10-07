import httpx
import pytest

from services import zte_client


class AlwaysTimeout(httpx.BaseTransport):
    def handle_request(self, request: httpx.Request) -> httpx.Response:  # type: ignore[override]
        raise httpx.ReadTimeout("timeout", request=request)


def test_request_timeout_translates_to_custom_error():
    client = zte_client.ZTEClient("http://example", transport=AlwaysTimeout())
    client._session.authenticated = True
    client._session.cookie = "SESSIONID=mock"

    with pytest.raises(zte_client.TimeoutError):
        client.request("/foo")


def test_request_raises_auth_error_on_401():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"error": "auth"})

    client = zte_client.ZTEClient("http://example", transport=httpx.MockTransport(handler))
    client._session.authenticated = True
    client._session.cookie = "SESSIONID=mock"

    with pytest.raises(zte_client.AuthenticationError):
        client.request("/foo")


def test_request_raises_parse_error_for_invalid_json():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text="not-json")

    client = zte_client.ZTEClient("http://example", transport=httpx.MockTransport(handler))
    client._session.authenticated = True
    client._session.cookie = "SESSIONID=mock"

    with pytest.raises(zte_client.ResponseParseError):
        client.request("/foo")
