from click.testing import CliRunner

from cli import zte as cli_module
from services import zte_client


def test_discover_defaults_to_get_when_no_payload(monkeypatch):
    runner = CliRunner()
    calls = {}

    class DummyClient:
        def __init__(self, host: str, **_: object) -> None:
            calls["host"] = host

        def login(self, password: str) -> None:
            calls["password"] = password

        def request(
            self, path: str, method: str, payload: str | None = None, expects: str = "json"
        ):
            calls["path"] = path
            calls["method"] = method
            calls["payload"] = payload
            return {"status": "ok"}

    monkeypatch.setattr(zte_client, "ZTEClient", DummyClient)
    result = runner.invoke(
        cli_module.cli,
        [
            "discover",
            "--host",
            "http://192.168.0.1",
            "--password",
            "secret",
            "--path",
            "goform/test",
        ],
    )

    assert result.exit_code == 0, result.output
    assert calls["method"] == "GET"
    assert calls["payload"] is None
