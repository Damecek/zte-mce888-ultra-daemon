"""Contract test ensuring --target-file writes Markdown with request/response details."""

from __future__ import annotations

from collections.abc import Callable
import json
from pathlib import Path
from typing import Any

from click.testing import CliRunner
import pytest

from zte_daemon.cli.main import cli


class StubClient:
    def __init__(self, *, on_request: Callable[[str, str, Any | None], dict[str, Any]]) -> None:
        """
        Initialize the StubClient with a callback used to handle simulated requests.
        
        Parameters:
            on_request (Callable[[str, str, Any | None], dict[str, Any]]): 
                A callable that will be invoked for each client request with arguments
                (path, method, payload) and should return a dictionary representing the
                mocked response. The callable's return value is used as the client's
                response to requests.
        """
        self._on_request = on_request

    def __enter__(self) -> "StubClient":
        """
        Enter the context and provide the StubClient instance.
        
        Returns:
            self (StubClient): The same StubClient instance to be used within the `with` block.
        """
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:  # pragma: no cover - trivial
        """
        Indicate that exceptions raised inside the context manager are not suppressed.
        
        Returns:
            bool: `False` to propagate exceptions raised in the with-block (do not suppress them).
        """
        return False

    def login(self, password: str) -> bool:
        """
        Authenticate with the client using the provided password.
        
        Returns:
            True if authentication succeeded, False otherwise.
        """
        return True

    def request(
        self,
        path: str,
        *,
        method: str,
        payload: Any | None,
        expects: str,
    ) -> dict[str, Any]:
        """
        Forward a request to the configured on_request callback and return its response.
        
        Parameters:
            path (str): The request path or endpoint.
            method (str): The HTTP method to use (e.g., "GET", "POST").
            payload (Any | None): The request payload, or None if there is no body.
            expects (str): A hint for the expected response format or type.
        
        Returns:
            dict[str, Any]: The response dictionary returned by the on_request callback.
        """
        return self._on_request(path, method, payload)


@pytest.fixture()
def runner() -> CliRunner:
    """
    Provide a CliRunner instance for invoking the application's CLI in tests.
    
    Returns:
        CliRunner: A new CliRunner configured for running command-line commands in test environments.
    """
    return CliRunner()


def test_target_file_writes_markdown(tmp_path: Path, runner: CliRunner, monkeypatch: pytest.MonkeyPatch) -> None:
    """
    Verify the `discover` CLI command writes a Markdown target file with request/response details and a JSON snapshot containing metadata and response data.
    
    This test replaces the real ZTE client with a stub that captures the outgoing request and returns a canned response, invokes the CLI with a --target-file path, and asserts:
    - the command exits successfully,
    - the target Markdown file exists and includes a Request section, the HTTP method, the payload, the response status, and a Response section,
    - the CLI output contains the target file path,
    - a companion JSON snapshot file exists and its `metadata` includes the request method and path and its `data` includes the response status.
    
    Parameters:
    	tmp_path (Path): Temporary directory provided by pytest for file outputs.
    	runner (CliRunner): Click test runner fixture used to invoke the CLI.
    	monkeypatch (pytest.MonkeyPatch): Fixture used to substitute the ZTE client with a stub.
    """
    def capture(path: str, method: str, payload: Any | None) -> dict[str, Any]:
        assert method == "POST"
        assert payload == {"foo": "bar"}
        return {"status": "ok", "data": [1, 2, 3]}

    import importlib

    discover_mod = importlib.import_module("zte_daemon.cli.commands.discover")
    monkeypatch.setattr(
        discover_mod,
        "ZTEClient",
        lambda host, **_: StubClient(on_request=capture),
    )

    target_file = tmp_path / "docs" / "discover" / "lan_station_list.md"

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
            "--target-file",
            str(target_file),
        ],
        catch_exceptions=False,
    )

    assert result.exit_code == 0
    assert target_file.exists()
    content = target_file.read_text()
    assert "## Request" in content
    assert "Method: POST" in content
    assert '"foo": "bar"' in content
    assert '"status": "ok"' in content
    assert "## Response" in content
    assert str(target_file) in result.output
    snapshot_file = target_file.with_suffix(".json")
    assert snapshot_file.exists()
    payload = json.loads(snapshot_file.read_text())
    assert payload["metadata"]["method"] == "POST"
    assert payload["metadata"]["path"] == "goform/example"
    assert payload["data"]["status"] == "ok"