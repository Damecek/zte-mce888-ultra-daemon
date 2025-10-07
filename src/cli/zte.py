"""Click CLI exposing modem discovery utilities."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import click
import httpx

from lib import logging_setup, markdown_io, snapshots
from services.zte_client import (
    AuthenticationError,
    RequestError,
    ResponseParseError,
    TimeoutError,
    ZTEClient,
)
from zte_daemon.cli.commands.read import read_command
from zte_daemon.cli.commands.run import run_command


@click.group(name="zte", help="ZTE MC888 modem utilities")
@click.version_option(message="%(version)s")
def cli() -> None:
    """Root CLI group."""
    logging_setup.configure()


@cli.command(name="discover", help="Invoke modem REST endpoints and capture responses")
@click.option("--host", default="http://192.168.0.1", show_default=True, help="Modem host URL")
@click.option("--password", required=True, help="Admin password")
@click.option("--path", required=True, help="Relative endpoint path")
@click.option("--payload", help="Optional payload (JSON string)")
@click.option(
    "--method",
    type=click.Choice(["GET", "POST"], case_sensitive=False),
    help="Override HTTP method",
)
@click.option("--target-file", type=click.Path(path_type=Path), help="Write Markdown example to this file")
def discover(
    host: str,
    password: str,
    path: str,
    payload: Optional[str],
    method: Optional[str],
    target_file: Optional[Path],
) -> None:
    effective_method = method.upper() if method else ("POST" if payload else "GET")

    try:
        client = ZTEClient(host)
    except httpx.ConnectError as exc:  # pragma: no cover - defensive: instantiation may not raise
        raise click.ClickException(f"Unable to connect to modem host: {exc}") from exc

    try:
        client.login(password)
        response = client.request(path, method=effective_method, payload=payload, expects="json")
    except httpx.ConnectError as exc:
        raise click.ClickException("Unable to connect to modem host") from exc
    except TimeoutError as exc:
        raise click.ClickException(f"Request timed out: {exc}") from exc
    except AuthenticationError as exc:
        raise click.ClickException(str(exc)) from exc
    except ResponseParseError as exc:
        raise click.ClickException(f"Failed to parse modem response: {exc}") from exc
    except RequestError as exc:
        raise click.ClickException(str(exc)) from exc

    if target_file:
        target_path = target_file if target_file.is_absolute() else Path.cwd() / target_file
        markdown_io.write_discover_example(
            target_path,
            host=host,
            path=path,
            method=effective_method,
            payload=payload,
            response=response,
        )
        snapshots.save_snapshot(
            target_path.parent,
            name=target_path.stem,
            request={
                "host": host,
                "path": path,
                "method": effective_method,
                "payload": payload,
            },
            response=response,
        )
        click.echo(str(target_path))
        return

    if isinstance(response, (dict, list)):
        click.echo(json.dumps(response, indent=2, sort_keys=True))
    else:
        click.echo(response)


cli.add_command(run_command)
cli.add_command(read_command)
