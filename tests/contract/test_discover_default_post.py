"""Contract test verifying payload implies POST by default."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from click.testing import CliRunner
import pytest

from zte_daemon.cli.main import cli


class StubClient:
    def __init__(self, *, on_request: Callable[[str, str, Any | None], None]) -> None:
        """
        Initialize the StubClient with a callback to receive intercepted request details.
        
        Parameters:
        	on_request (Callable[[str, str, Any | None], None]): Callback invoked with (path, method, payload) when the client.request method is called.
        """
        self._on_request = on_request

    def __enter__(self) -> "StubClient":
        """
        Enter the context and return the StubClient instance.
        
        Returns:
            self (StubClient): The context manager instance.
        """
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:  # pragma: no cover - trivial
        """
        Context manager exit handler that does not suppress exceptions.
        
        Returns:
            False: Indicates any exception raised in the context should be propagated.
        """
        return False

    def login(self, password: str) -> bool:
        """
        Validate that the provided password equals the expected secret.
        
        Parameters:
            password (str): Password to verify.
        
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
        Invoke the configured request callback and return a fixed success response.
        
        Parameters:
            path (str): The request path being sent.
            method (str): The HTTP method to use for the request (e.g., "GET", "POST").
            payload (Any | None): The request payload, or None if there is none.
            expects (str): Expected response format; must be "json".
        
        Returns:
            dict[str, Any]: A fixed response object {"result": "ok"}.
        
        Notes:
            - Calls the instance's configured on-request callback with (path, method, payload).
            - The function asserts that `expects` is "json".
        """
        self._on_request(path, method, payload)
        assert expects == "json"
        return {"result": "ok"}


@pytest.fixture()
def runner() -> CliRunner:
    """
    Provide a CliRunner instance for invoking the application's CLI in tests.
    
    Returns:
        runner (CliRunner): A test runner for invoking CLI commands and capturing output.
    """
    return CliRunner()


def test_discover_defaults_to_post_when_payload_present(
    runner: CliRunner, monkeypatch: pytest.MonkeyPatch
) -> None:
    """
    Verify the discover CLI command uses HTTP POST and forwards the parsed JSON payload when a payload is provided.
    
    This test runs the CLI's discover command with a JSON payload and asserts the command exits successfully, the request method is "POST", and the forwarded payload is the parsed dictionary.
    """
    captured: dict[str, Any] = {}

    def capture(path: str, method: str, payload: Any | None) -> None:
        """
        Record request details into the module-level `captured` mapping.
        
        Parameters:
            path (str): Request path to store under the "path" key.
            method (str): HTTP method to store under the "method" key.
            payload (Any | None): Request payload to store under the "payload" key.
        """
        captured.update({"path": path, "method": method, "payload": payload})

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
            "--payload",
            '{"foo": "bar"}',
        ],
        catch_exceptions=False,
    )

    assert result.exit_code == 0
    assert captured["method"] == "POST"
    assert captured["payload"] == {"foo": "bar"}