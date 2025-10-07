from __future__ import annotations

import pytest
from click.testing import CliRunner

from cli.zte import cli


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


def test_read_command_returns_metric_value(runner: CliRunner) -> None:
    result = runner.invoke(cli, ["read", "RSRP"], catch_exceptions=False)
    assert result.exit_code == 0
    output = result.output
    assert "RSRP" in output
    assert "-85" in output
    assert "Telekom" not in output  # ensure metric-specific


def test_read_command_rejects_unknown_metric(runner: CliRunner) -> None:
    result = runner.invoke(cli, ["read", "SNR"], catch_exceptions=False)
    assert result.exit_code != 0
    assert "Unknown metric" in result.output
