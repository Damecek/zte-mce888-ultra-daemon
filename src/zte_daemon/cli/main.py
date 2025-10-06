"""CLI entry point for the ZTE MC888 Ultra daemon mock."""
from __future__ import annotations

import click

from zte_daemon.cli.commands.read import read_command
from zte_daemon.cli.commands.run import run_command

@click.group(name="zte", help="ZTE MC888 Ultra daemon developer utilities.")
@click.version_option(message="%(version)s")
def cli() -> None:
    """Root CLI group."""


def _register_commands() -> None:
    cli.add_command(run_command)
    cli.add_command(read_command)

_register_commands()

__all__ = ["cli"]
