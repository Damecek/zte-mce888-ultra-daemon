"""CLI contract test: discover defaults to GET when no payload is provided."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from click.testing import CliRunner
import pytest

from zte_daemon.cli.main import cli


class StubClient:
    def __init__(self, *, on_request: Callable[[str, str, Any | None], None]) -> None:
        """
        Initialize the stub client with a callback to receive captured request details.
        
        Parameters:
            on_request (Callable[[str, str, Any | None], None]): Callback invoked with three arguments — `path` (request path), `method` (HTTP method), and `payload` (request payload or None) — whenever the stub client's request method is called.
        """
        self._on_request = on_request

    def __enter__(self) -> "StubClient":
        """
        Enter the context manager and return the client instance.
        
        Returns:
            self (StubClient): The StubClient instance to be used inside the context.
        """
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:  # pragma: no cover - trivial
        """
        Context-manager exit handler that does not suppress exceptions.
        
        Returns:
            False: Indicating any exception raised in the with-block should be propagated.
        """
        return False

    def login(self, password: str) -> bool:  # pragma: no cover - exercised in contract tests
        """
        Validate that the provided password equals the stubbed secret and indicate successful login.
        
        Parameters:
            password (str): Password to validate; must be "secret" for successful authentication.
        
        Returns:
            bool: True if the password equals "secret".
        """
        assert password == "secret"
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
        Record a request via the stored callback and return a canned JSON-like response.
        
        Calls the instance's request callback with the provided path, method, and payload and asserts that the expected response format is "json".
        
        Parameters:
            path (str): Request path.
            method (str): HTTP method to use (e.g., "GET", "POST").
            payload (Any | None): Request payload or None when there is no body.
            expects (str): Expected response format; must be "json".
        
        Returns:
            response (dict[str, Any]): A stubbed response dictionary with {"result": "ok"}.
        """
        self._on_request(path, method, payload)
        assert expects == "json"
        return {"result": "ok"}


@pytest.fixture()
def runner() -> CliRunner:
    """
    Provide a Click CliRunner for invoking CLI commands in tests.
    
    Returns:
        cli_runner (CliRunner): A CliRunner instance for running CLI commands and capturing output and exit codes.
    """
    return CliRunner()


def test_discover_defaults_to_get(runner: CliRunner, monkeypatch: pytest.MonkeyPatch) -> None:
    """
    Verifies the CLI discover command defaults to using the GET method when no payload is provided.
    
    Injects a stubbed client that records the request, invokes the discover command with host, password, and path, and asserts the recorded path is "goform/example", the method is "GET", and the payload is None.
    """
    captured: dict[str, Any] = {}

    def capture(path: str, method: str, payload: Any | None) -> None:
        """
        Record request details into the shared `captured` dictionary used by the test.
        
        Parameters:
            path (str): Request path provided to the discover command.
            method (str): HTTP method used for the request (e.g., "GET", "POST").
            payload (Any | None): Request payload, or `None` when no payload was provided.
        """
        captured.update({"path": path, "method": method, "payload": payload})

    # Delay import to allow ModuleNotFoundError to surface until implementation exists
    import importlib

    discover_mod = importlib.import_module("zte_daemon.cli.commands.discover")
    monkeypatch.setattr(
        discover_mod,
        "ZTEClient",
        lambda host, **_: StubClient(on_request=capture),
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
        ],
        catch_exceptions=False,
    )

    assert result.exit_code == 0
    assert captured["path"] == "goform/example"
    assert captured["method"] == "GET"
    assert captured["payload"] is None