from click.testing import CliRunner
import pytest

from zte_daemon.cli.main import cli


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


def test_top_level_help_includes_commands(runner: CliRunner) -> None:
    """
    Verify the top-level CLI help shows the expected usage line, version option, and listed commands.
    
    Asserts that the help output includes:
    - the common usage line for the CLI,
    - the version option description,
    - the "discover", "read", and "run" command entries with their expected short descriptions.
    """
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    output = result.output
    assert "Usage: zte [OPTIONS] COMMAND [ARGS]..." in output
    assert "--version  Show the version and exit." in output
    assert "discover  Discover modem REST endpoints and capture responses." in output
    assert "read      Read a modem metric via REST (e.g., RSRP1, provider, bands)." in output
    assert "run       Run the ZTE modem daemon with mocked MQTT publish loop." in output


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
    assert "--timeout FLOAT" in output
    assert "HTTP timeout in seconds for modem requests." in output


def test_read_command_help_matches_contract(runner: CliRunner) -> None:
    result = runner.invoke(cli, ["read", "--help"])
    assert result.exit_code == 0
    output = result.output
    assert "Usage: zte read [OPTIONS] METRIC" in output
    assert "METRIC" in output
    assert "Read a modem metric via REST" in output
    assert "--host TEXT" in output
    assert "Modem host or IP address." in output
    assert "--password TEXT" in output
    assert "Password used for modem REST authentication" in output
    assert "--timeout FLOAT" in output
    assert "HTTP timeout in seconds." in output