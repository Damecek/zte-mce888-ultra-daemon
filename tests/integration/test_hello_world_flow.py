from __future__ import annotations

from pathlib import Path

from click.testing import CliRunner

from zte_daemon.cli.main import cli


def test_run_then_read_flow(tmp_path: Path) -> None:
    runner = CliRunner()
    log_file = tmp_path / "zte.log"

    run_result = runner.invoke(
        cli,
        [
            "run",
            "--device-pass",
            "secret",
            "--log",
            "info",
            "--log-file",
            str(log_file),
            "--foreground",
        ],
        catch_exceptions=False,
    )

    assert run_result.exit_code == 0
    assert "Hello from the ZTE MC888 Ultra mock daemon!" in run_result.output
    assert log_file.exists()

    read_result = runner.invoke(cli, ["read", "Provider"], catch_exceptions=False)
    assert read_result.exit_code == 0
    assert "Provider: Telekom" in read_result.output
