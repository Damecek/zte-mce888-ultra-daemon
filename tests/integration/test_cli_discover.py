"""Integration tests for the `zte discover` command."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from click.testing import CliRunner
import httpx
import pytest

from zte_daemon.cli.main import cli
from zte_daemon.modem.zte_client import AuthenticationError, RequestError


class ScenarioClient:
    def __init__(self, *, scenario: str, on_request: Callable[[str, str, Any | None], None] | None = None) -> None:
        """
        Create a ScenarioClient configured to simulate a specific test scenario.
        
        Parameters:
            scenario (str): Name of the scenario to simulate. Expected values:
                - "network": simulate a network error when performing requests.
                - "auth-failure": simulate failed authentication on login.
                - "success": simulate normal successful interactions.
            on_request (Callable[[str, str, Any | None], None] | None): Optional callback invoked for each simulated request with arguments (path, method, payload). Used to observe requests made during tests.
        """
        self._scenario = scenario
        self._on_request = on_request

    def __enter__(self) -> "ScenarioClient":
        """
        Support context manager protocol by returning this ScenarioClient instance.
        
        Returns:
            ScenarioClient: The same client instance to be used within the context manager.
        """
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:  # pragma: no cover - trivial
        """
        Context-manager exit handler that performs no special handling.
        
        Returns:
            bool: `False` to indicate any exception should not be suppressed by the context manager.
        """
        return False

    def login(self, password: str) -> bool:
        """
        Attempt to authenticate with the given password for this ScenarioClient.
        
        Parameters:
            password (str): The password used to authenticate.
        
        Returns:
            True if authentication succeeds.
        
        Raises:
            AuthenticationError: If the configured scenario simulates an authentication failure.
        """
        if self._scenario == "auth-failure":
            raise AuthenticationError("invalid credentials")
        return True

    def request(
        self,
        path: str,
        *,
        method: str,
        payload: Any | None,
        expects: str,
    ) -> Any:
        """
        Simulate sending a request to the modem according to the test scenario.
        
        Parameters:
            path (str): Request path on the modem.
            method (str): HTTP method to use for the request.
            payload (Any | None): Request payload or None.
            expects (str): Expected response content type or schema identifier.
        
        Returns:
            Any: Mocked response; in the success scenario a dict with keys `"status"` and `"path"`.
        
        Raises:
            RequestError: When the scenario is `"network"`, to indicate the modem is unreachable.
        """
        if self._scenario == "network":
            raise RequestError("network unreachable") from httpx.ConnectError(
                "boom", request=httpx.Request(method, httpx.URL("http://modem"))
            )
        if self._on_request:
            self._on_request(path, method, payload)
        return {"status": "ok", "path": path}


@pytest.fixture()
def runner() -> CliRunner:
    """
    Create a fresh Click CliRunner for invoking CLI commands in tests.
    
    Returns:
        CliRunner: a new CliRunner instance
    """
    return CliRunner()


def test_discover_reports_network_error(runner: CliRunner, monkeypatch: pytest.MonkeyPatch) -> None:
    """
    Verifies the CLI "discover" command reports a network error when the modem is unreachable.
    
    Patches the command's ZTEClient to simulate a network failure, invokes the CLI with host, password, and path, and asserts the process exits with a non-zero status and prints "Unable to reach modem".
    """
    import importlib

    discover_mod = importlib.import_module("zte_daemon.cli.commands.discover")
    monkeypatch.setattr(
        discover_mod,
        "ZTEClient",
        lambda host, **_: ScenarioClient(scenario="network"),
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

    assert result.exit_code != 0
    assert "Unable to reach modem" in result.output


def test_discover_reports_auth_failure(runner: CliRunner, monkeypatch: pytest.MonkeyPatch) -> None:
    import importlib

    discover_mod = importlib.import_module("zte_daemon.cli.commands.discover")
    monkeypatch.setattr(
        discover_mod,
        "ZTEClient",
        lambda host, **_: ScenarioClient(scenario="auth-failure"),
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

    assert result.exit_code != 0
    assert "Authentication failed" in result.output


def test_discover_successful_flow_outputs_json(runner: CliRunner, monkeypatch: pytest.MonkeyPatch) -> None:
    """
    Verifies the discover command performs a successful request and prints JSON output.
    
    Runs the CLI discover flow with a mocked ZTEClient that captures the outgoing request; asserts the command exits with code 0, the captured request is {"path": "goform/example", "method": "GET", "payload": None}, and the command output contains the JSON fragment '"status": "ok"'.
    """
    captured: dict[str, Any] = {}

    def capture(path: str, method: str, payload: Any | None) -> None:
        """
        Store the given request details into the shared `captured` mapping.
        
        Parameters:
            path (str): Request path to record.
            method (str): HTTP method to record.
            payload (Any | None): Request payload to record; may be None.
        """
        captured.update({"path": path, "method": method, "payload": payload})

    import importlib

    discover_mod = importlib.import_module("zte_daemon.cli.commands.discover")
    monkeypatch.setattr(
        discover_mod,
        "ZTEClient",
        lambda host, **_: ScenarioClient(scenario="success", on_request=capture),
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
    assert captured == {"path": "goform/example", "method": "GET", "payload": None}
    assert '"status": "ok"' in result.output