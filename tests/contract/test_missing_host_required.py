"""Contract tests ensuring host option is required for CLI commands."""

from __future__ import annotations

from click.testing import CliRunner
import pytest

from zte_daemon.cli.main import cli


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


def test_discover_requires_host(runner: CliRunner) -> None:
    result = runner.invoke(
        cli,
        [
            "discover",
            "--password",
            "secret",
            "--path",
            "goform/example",
        ],
    )

    assert result.exit_code != 0
    assert "--host" in result.output


def test_read_requires_host(runner: CliRunner) -> None:
    result = runner.invoke(
        cli,
        [
            "read",
            "rsrp1",
        ],
    )

    assert result.exit_code != 0
    assert "--host" in result.output
