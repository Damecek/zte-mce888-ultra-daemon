import httpx
import pytest

from services import zte_client


class RecordingTransport(httpx.BaseTransport):
    def __init__(self) -> None:
        self.state: dict[str, bool] = {"logged_in": False}

    def handle_request(self, request: httpx.Request) -> httpx.Response:  # type: ignore[override]
        if request.method == "GET" and request.url.path == "/goform/goform_get_cmd_process":
            params = dict(request.url.params)
            if params.get("cmd") == "wa_inner_version,cr_version,RD,LD":
                assert params.get("multi_data") == "1"
                data = {
                    "wa_inner_version": "MC888-TEST",
                    "cr_version": "V1.0.0",
                    "RD": "salt-RD",
                    "LD": "salt-LD",
                }
                return httpx.Response(200, json=data)

        if request.method == "POST" and request.url.path == "/goform/goform_set_cmd_process":
            form = dict(httpx.QueryParams(request.content.decode()))
            assert form == {
                "isTest": "false",
                "goformId": "LOGIN",
                "password": zte_client.sha256_hex(zte_client.sha256_hex("password") + "salt-LD"),
                "AD": zte_client.sha256_hex(zte_client.sha256_hex("MC888-TESTV1.0.0") + "salt-RD"),
            }
            self.state["logged_in"] = True
            headers = {"Set-Cookie": "SESSIONID=abc123; Path=/; HttpOnly"}
            return httpx.Response(200, json={"result": "0"}, headers=headers)

        if request.url.path == "/goform/protected" and request.method == "GET":
            if request.headers.get("Cookie") == "SESSIONID=abc123" and self.state["logged_in"]:
                return httpx.Response(200, json={"ok": True})
            return httpx.Response(403, json={"error": "forbidden"})

        raise AssertionError(f"Unexpected request: {request.method} {request.url}")


def test_login_and_authenticated_request_flow():
    transport = RecordingTransport()
    client = zte_client.ZTEClient("http://192.168.0.1", transport=transport)

    with pytest.raises(zte_client.AuthenticationError):
        client.request("/goform/protected", method="GET")

    client.login("password")

    response = client.request("/goform/protected", method="GET")
    assert response == {"ok": True}
