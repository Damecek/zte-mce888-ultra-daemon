import re

import pytest
from click.testing import CliRunner

from cli.zte import cli


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


def test_top_level_help_includes_commands(runner: CliRunner) -> None:
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    output = result.output
    assert "Usage: zte [OPTIONS] COMMAND [ARGS]..." in output
    assert "--version  Show the version and exit." in output
    assert re.search(
        r"^\s*run\s+Run the ZTE modem daemon with mocked MQTT publish loop\.",
        output,
        flags=re.M,
    )
    assert re.search(r"^\s*read\s+Read a modem metric by identifier\.", output, flags=re.M)


def test_run_command_help_matches_contract(runner: CliRunner) -> None:
    result = runner.invoke(cli, ["run", "--help"])
    assert result.exit_code == 0
    output = result.output
    assert "Usage: zte run [OPTIONS]" in output
    assert "--device-host TEXT" in output
    assert "Local modem address" in output
    assert "[default: 192.168.0.1]" in output
    assert "--device-pass TEXT" in output
    assert "Password used for modem REST authentication" in output
    assert "[required]" in output
    assert "--log [debug|info|warn|error]" in output
    assert "Log level for stdout and file handlers" in output
    assert "[default: info]" in output
    assert "--foreground" in output
    assert "Run in foreground (runs in background" in output
    assert "--log-file PATH" in output
    assert "Optional log file destination" in output
    assert "--mqtt-host TEXT" in output
    assert "Placeholder broker address" in output
    assert "--mqtt-topic TEXT" in output
    assert "Topic used in mock publish" in output
    assert "[default: zte-modem]" in output
    assert "--mqtt-user TEXT" in output
    assert "MQTT username placeholder." in output
    assert "--mqtt-password TEXT" in output
    assert "MQTT password placeholder (never logged)." in output


def test_read_command_help_matches_contract(runner: CliRunner) -> None:
    result = runner.invoke(cli, ["read", "--help"])
    assert result.exit_code == 0
    output = result.output
    assert "Usage: zte read [OPTIONS] METRIC" in output
    assert "METRIC" in output
    assert "Metric identifier (e.g., lte.rsrp1, nr5g.pci, wan_ip)." in output
