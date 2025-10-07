"""Contract test ensuring JSON payloads are encoded with appropriate headers."""

from __future__ import annotations

import json
from typing import Any

from click.testing import CliRunner
import httpx
import pytest

from zte_daemon.cli.main import cli
from zte_daemon.modem.zte_client import ZTEClient


class RecordingClient(ZTEClient):
    def __init__(self, host: str, recorder: dict[str, Any]) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            recorder["method"] = request.method
            recorder["headers"] = dict(request.headers)
            recorder["body"] = request.content.decode()
            return httpx.Response(200, json={"status": "ok"})

        super().__init__(host=host, transport=httpx.MockTransport(handler))
        self._authenticated = True  # type: ignore[attr-defined]

    def login(self, password: str) -> bool:  # pragma: no cover - behaviour validated by contract tests
        self._authenticated = True  # type: ignore[attr-defined]
        return True


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


def test_payload_sets_json_header_and_body(runner: CliRunner, monkeypatch: pytest.MonkeyPatch) -> None:
    recorded: dict[str, Any] = {}

    import importlib

    discover_mod = importlib.import_module("zte_daemon.cli.commands.discover")
    monkeypatch.setattr(
        discover_mod,
        "ZTEClient",
        lambda host, **_: RecordingClient(host, recorded),
    )

    result = runner.invoke(
        cli,
        [
            "discover",
            "--host",
            "192.168.0.1",
            "--password",
            "secret",
            "--path",
            "goform/example",
            "--payload",
            '{"foo": "bar"}',
        ],
        catch_exceptions=False,
    )

    assert result.exit_code == 0
    assert recorded["method"] == "POST"
    headers = recorded["headers"]
    assert headers.get("content-type") == "application/json"
    assert json.loads(recorded["body"]) == {"foo": "bar"}
