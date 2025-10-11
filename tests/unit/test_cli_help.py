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
        r"^\s*run\s+Run the ZTE router daemon that responds to MQTT metric requests\.",
        output,
        flags=re.M,
    )
    assert re.search(r"^\s*read\s+Read a router metric by identifier\.", output, flags=re.M)


def test_run_command_help_matches_contract(runner: CliRunner) -> None:
    result = runner.invoke(cli, ["run", "--help"])
    assert result.exit_code == 0
    output = result.output
    assert "Usage: zte run [OPTIONS]" in output
    assert "--router-host TEXT" in output
    assert "Router host URL" in output
    # Default may be omitted in help when option is required
    assert "--router-password TEXT" in output
    assert "Router admin password" in output
    assert "[required]" in output
    assert "--log [debug|info|warn|error]" in output
    assert "Log level for stdout and file handlers" in output
    assert "[default: warn]" in output
    assert "--foreground" in output
    assert "Run in foreground (default)." in output
    assert "--log-file PATH" in output
    assert "Optional log file destination" in output
    assert "--mqtt-host TEXT" in output
    assert "MQTT broker hostname or IP address." in output
    assert "--mqtt-topic TEXT" in output
    assert "Root topic for requests." in output
    assert "[default: zte]" in output
    assert "--mqtt-username TEXT" in output
    assert "MQTT username if authentication is required." in output
    assert "--mqtt-password TEXT" in output
    assert "MQTT password if authentication is required." in output


def test_read_command_help_matches_contract(runner: CliRunner) -> None:
    result = runner.invoke(cli, ["read", "--help"])
    assert result.exit_code == 0
    output = result.output
    assert "Usage: zte read [OPTIONS] METRIC" in output
    assert "METRIC" in output
    assert "Metric identifier (e.g., lte.rsrp1, nr5g.pci, wan_ip)." in output
