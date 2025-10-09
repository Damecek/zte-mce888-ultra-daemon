from pathlib import Path

from click.testing import CliRunner

from cli import zte as cli_module
from lib import markdown_io
from services import zte_client


def test_discover_writes_target_markdown(monkeypatch, tmp_path):
    runner = CliRunner()
    calls = {}

    class DummyClient:
        def __init__(self, host: str, **_: object) -> None:
            calls["host"] = host

        def login(self, password: str) -> None:
            calls["password"] = password

        def request(self, path: str, method: str, payload: str | None = None, expects: str = "json"):
            calls["path"] = path
            calls["method"] = method
            calls["payload"] = payload
            return {"data": [1, 2, 3]}

    def fake_write(target_file: Path, host: str, path: str, method: str, payload: str | None, response):
        calls["target_file"] = Path(target_file)
        calls["markdown_host"] = host
        Path(target_file).write_text("# example\n")

    target_file = tmp_path / "docs" / "discover" / "example.md"
    target_file.parent.mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(zte_client, "ZTEClient", DummyClient)
    monkeypatch.setattr(markdown_io, "write_discover_example", fake_write)

    result = runner.invoke(
        cli_module.cli,
        [
            "discover",
            "--router-host",
            "http://192.168.0.1",
            "--router-password",
            "secret",
            "--path",
            "goform/test",
            "--target-file",
            str(target_file),
        ],
    )

    assert result.exit_code == 0, result.output
    assert calls["target_file"] == target_file
    assert calls["markdown_host"] == "http://192.168.0.1"
    assert target_file.read_text() == "# example\n"
    assert str(target_file) in result.output
