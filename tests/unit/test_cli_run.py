from collections import deque
from typing import Any

import pytest
from click.testing import CliRunner

from cli.commands import run as run_module
from cli.zte import cli


@pytest.fixture()
def runner() -> CliRunner:
    """
    Provide a pytest fixture that supplies a Click CliRunner for invoking CLI commands in tests.
    
    Returns:
        CliRunner: A CliRunner instance for simulating command-line invocations.
    """
    return CliRunner()


def test_run_command_invokes_async_daemon(monkeypatch: pytest.MonkeyPatch, runner: CliRunner) -> None:
    calls: deque[dict[str, Any]] = deque()

    async def fake_run_daemon(**kwargs: Any) -> None:
        """
        Record received keyword arguments by appending them to the surrounding `calls` deque.
        
        Parameters:
            **kwargs: Any
                Keyword arguments representing a simulated daemon invocation; the full kwargs
                mapping is appended to the module-scoped `calls` deque as a single entry.
        """
        calls.append(kwargs)

    monkeypatch.setattr(run_module, "_run_daemon", fake_run_daemon)

    result = runner.invoke(
        cli,
        [
            "run",
            "--router-host",
            "192.168.0.1",
            "--router-password",
            "test-pass",
            "--log",
            "info",
            "--log-file",
            "run.log",
            "--mqtt-host",
            "192.168.0.50",
            "--mqtt-port",
            "1883",
            "--mqtt-topic",
            "zte-modem",
            "--mqtt-username",
            "user",
            "--mqtt-password",
            "pass",
            "--foreground",
        ],
        catch_exceptions=False,
    )

    assert result.exit_code == 0
    assert calls, "async daemon should have been invoked"
    kwargs = calls.pop()
    assert kwargs["router_host"] == "192.168.0.1"
    assert kwargs["router_password"] == "test-pass"
    assert kwargs["mqtt_host"] == "192.168.0.50"
    assert kwargs["mqtt_port"] == 1883
    assert kwargs["mqtt_topic"] == "zte-modem"
    assert kwargs["mqtt_username"] == "user"
    assert kwargs["mqtt_password"] == "pass"
    assert kwargs["foreground"] is True