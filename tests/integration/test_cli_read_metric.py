"""Integration tests for `zte read` command."""

from __future__ import annotations

from typing import Any

from click.testing import CliRunner
import httpx
import pytest

from zte_daemon.cli.main import cli
from zte_daemon.modem.zte_client import RequestError


class SnapshotStub:
    def __init__(self, metrics: dict[str, Any]) -> None:
        """
        Initialize the snapshot stub with a mapping of metric names to their values.
        
        Parameters:
            metrics (dict[str, Any]): Mapping where keys are metric identifiers and values are the corresponding metric values; stored for later retrieval.
        """
        self._metrics = metrics

    def metric_map(self) -> dict[str, Any]:
        """
        Provide the stored metrics mapping.
        
        Returns:
            dict[str, Any]: Dictionary mapping metric names to their values as held by this snapshot.
        """
        return self._metrics


class StubClient:
    def __init__(self, snapshot: SnapshotStub) -> None:
        """
        Initialize the client with a preconfigured snapshot used to simulate modem metrics.
        
        Parameters:
            snapshot (SnapshotStub): SnapshotStub containing the metric map this client will provide.
        """
        self._snapshot = snapshot

    def __enter__(self) -> "StubClient":
        """
        Enter the context manager and return the StubClient instance.
        
        Returns:
            StubClient: The client instance to be used inside the context.
        """
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        """
        Context manager exit that does not suppress exceptions.
        
        Parameters:
            exc_type (Optional[type]): The exception type raised in the context, or None if no exception occurred.
            exc (Optional[BaseException]): The exception instance raised in the context, or None if no exception occurred.
            tb (Optional[types.TracebackType]): The traceback object for the exception, or None if no exception occurred.
        
        Returns:
            bool: `False` to indicate any exception raised inside the context should be propagated.
        """
        return False

    def login(self, password: str) -> bool:
        """
        Simulate authentication with the modem using the provided password.
        
        Parameters:
            password (str): The modem login password.
        
        Returns:
            bool: `True` if authentication succeeded, `False` otherwise. This stub always returns `True`.
        """
        return True

    def fetch_snapshot(self) -> SnapshotStub:
        """
        Return the stored snapshot stub representing modem metrics.
        
        Returns:
            SnapshotStub: The snapshot previously provided to this client stub.
        """
        return self._snapshot


class NetworkErrorClient:
    def __enter__(self) -> "NetworkErrorClient":
        """
        Enter the context manager and provide the NetworkErrorClient instance for use within a `with` block.
        
        Returns:
            NetworkErrorClient: The client instance entered by the context manager.
        """
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        """
        Context manager exit that does not suppress exceptions.
        
        Parameters:
            exc_type (Optional[type]): The exception type raised in the context, or None if no exception occurred.
            exc (Optional[BaseException]): The exception instance raised in the context, or None if no exception occurred.
            tb (Optional[types.TracebackType]): The traceback object for the exception, or None if no exception occurred.
        
        Returns:
            bool: `False` to indicate any exception raised inside the context should be propagated.
        """
        return False

    def login(self, password: str) -> bool:
        """
        Simulate authentication with the modem using the provided password.
        
        Parameters:
            password (str): The modem login password.
        
        Returns:
            bool: `True` if authentication succeeded, `False` otherwise. This stub always returns `True`.
        """
        return True

    def fetch_snapshot(self) -> SnapshotStub:
        """
        Simulate a network failure when fetching a snapshot.
        
        Raises:
            RequestError: Always raised with message "network unreachable" and caused by an underlying httpx.ConnectError that mimics a connection failure to the modem.
        """
        raise RequestError("network unreachable") from httpx.ConnectError(
            "boom",
            request=httpx.Request("GET", httpx.URL("http://modem")),
        )


@pytest.fixture()
def runner() -> CliRunner:
    """
    Provide a CliRunner used to invoke the CLI and capture its output in tests.
    
    Returns:
        CliRunner: A new CliRunner instance for running CLI commands and inspecting results.
    """
    return CliRunner()


def test_read_outputs_metric_value(runner: CliRunner, monkeypatch: pytest.MonkeyPatch) -> None:
    import importlib

    read_mod = importlib.import_module("zte_daemon.cli.commands.read")
    monkeypatch.setattr(
        read_mod,
        "ZTEClient",
        lambda host, **_: StubClient(SnapshotStub({"rsrp1": -85, "provider": "TestNet"})),
    )

    result = runner.invoke(
        cli,
        [
            "read",
            "RSRP1",
            "--host",
            "192.168.0.1",
            "--password",
            "secret",
        ],
        catch_exceptions=False,
    )

    assert result.exit_code == 0
    assert "RSRP1: -85" in result.output


def test_read_unknown_metric_produces_error(runner: CliRunner, monkeypatch: pytest.MonkeyPatch) -> None:
    """
    Verifies that invoking the CLI read command with an unknown metric results in a non-zero exit code and an "Unknown metric" error message.
    
    Invokes the CLI with an invalid metric name and asserts the command fails and emits the expected error text.
    """
    import importlib

    read_mod = importlib.import_module("zte_daemon.cli.commands.read")
    monkeypatch.setattr(
        read_mod,
        "ZTEClient",
        lambda host, **_: StubClient(SnapshotStub({"rsrp1": -85})),
    )

    result = runner.invoke(
        cli,
        [
            "read",
            "invalid",
            "--host",
            "192.168.0.1",
            "--password",
            "secret",
        ],
        catch_exceptions=False,
    )

    assert result.exit_code != 0
    assert "Unknown metric" in result.output


def test_read_reports_network_error(runner: CliRunner, monkeypatch: pytest.MonkeyPatch) -> None:
    import importlib

    read_mod = importlib.import_module("zte_daemon.cli.commands.read")
    monkeypatch.setattr(read_mod, "ZTEClient", lambda host, **_: NetworkErrorClient())

    result = runner.invoke(
        cli,
        [
            "read",
            "rsrp1",
            "--host",
            "192.168.0.1",
            "--password",
            "secret",
        ],
        catch_exceptions=False,
    )

    assert result.exit_code != 0
    assert "Unable to reach modem" in result.output