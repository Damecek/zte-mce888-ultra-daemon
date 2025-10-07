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
        """
        Initialize a ZTEClient that records outgoing HTTP request details into `recorder`.
        
        Parameters:
            host (str): Host address used to construct the client.
            recorder (dict[str, Any]): Mutable mapping where the client will store captured request data:
                - "method": HTTP method as a string.
                - "headers": dict of request headers.
                - "body": request body decoded to a string.
        
        """
        def handler(request: httpx.Request) -> httpx.Response:
            recorder["method"] = request.method
            recorder["headers"] = dict(request.headers)
            recorder["body"] = request.content.decode()
            return httpx.Response(200, json={"status": "ok"})

        super().__init__(host=host, transport=httpx.MockTransport(handler))
        self._authenticated = True  # type: ignore[attr-defined]

    def login(self, password: str) -> bool:  # pragma: no cover - behaviour validated by contract tests
        """
        Mark the client as authenticated and indicate a successful login.
        
        Parameters:
            password (str): Ignored by this test client; present to match the production API.
        
        Returns:
            bool: `True` to indicate authentication was successful.
        """
        self._authenticated = True  # type: ignore[attr-defined]
        return True


@pytest.fixture()
def runner() -> CliRunner:
    """
    Create a Click test runner for invoking CLI commands.
    
    Returns:
        CliRunner: a new CliRunner instance for use in tests.
    """
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