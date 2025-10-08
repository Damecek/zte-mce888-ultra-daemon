"""Click CLI exposing modem discovery utilities."""

from __future__ import annotations

import click

from cli.commands.discover import discover_command
from cli.commands.read import read_command
from cli.commands.run import run_command
from lib import (
    logging_setup,
    markdown_io,  # noqa: F401 - re-exported for tests via cli module
    snapshots,  # noqa: F401 - re-exported for tests via cli module
)


@click.group(name="zte", help="ZTE MC888 modem utilities")
@click.version_option(message="%(version)s")
def cli() -> None:
    """Root CLI group."""
    logging_setup.configure()

cli.add_command(discover_command)
cli.add_command(run_command)
cli.add_command(read_command)
