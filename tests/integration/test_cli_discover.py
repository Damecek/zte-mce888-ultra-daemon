import httpx
from click.testing import CliRunner

from cli import zte as cli_module
from services import zte_client


def test_discover_reports_unreachable_host(monkeypatch):
    runner = CliRunner()

    class FailingClient:
        def __init__(self, *args, **kwargs):
            raise httpx.ConnectError("boom", request=httpx.Request("GET", "http://example"))

    monkeypatch.setattr(zte_client, "ZTEClient", FailingClient)

    result = runner.invoke(
        cli_module.cli,
        ["discover", "--router-host", "http://example", "--router-password", "pw", "--path", "goform/test"],
    )

    assert result.exit_code != 0
    assert "unable to connect" in result.output.lower()


def test_discover_reports_auth_failure(monkeypatch):
    runner = CliRunner()

    class Client:
        def __init__(self, *args, **kwargs):
            pass

        def login(self, password: str) -> None:
            raise zte_client.AuthenticationError("bad credentials")

    monkeypatch.setattr(zte_client, "ZTEClient", Client)

    result = runner.invoke(
        cli_module.cli,
        ["discover", "--router-host", "http://example", "--router-password", "pw", "--path", "goform/test"],
    )

    assert result.exit_code != 0
    assert "bad credentials" in result.output


def test_discover_success_prints_response(monkeypatch):
    runner = CliRunner()

    class Client:
        def __init__(self, *args, **kwargs):
            pass

        def login(self, password: str) -> None:
            return None

        def request(self, path: str, method: str, payload=None, expects: str = "json"):
            return {"status": "ok"}

    monkeypatch.setattr(zte_client, "ZTEClient", Client)

    result = runner.invoke(
        cli_module.cli,
        ["discover", "--router-host", "http://example", "--router-password", "pw", "--path", "goform/test"],
    )

    assert result.exit_code == 0
    assert "status" in result.output
