"""Implementation of the `zte discover` command consolidated under commands/."""

from __future__ import annotations

import json
from pathlib import Path

import click
import httpx

from lib import markdown_io, snapshots
from lib.logging_setup import configure_logging, logging_options
from services.zte_client import (
    AuthenticationError,
    RequestError,
    ResponseParseError,
    TimeoutError,
    ZTEClient,
)


@click.command(name="discover", help="Invoke modem REST endpoints and capture responses")
@click.option("--host", default="http://192.168.0.1", show_default=True, help="Modem host URL")
@click.option("--password", required=True, help="Admin password")
@click.option("--path", required=True, help="Relative endpoint path")
@click.option("--payload", help="Optional payload (JSON string)")
@click.option(
    "--method",
    type=click.Choice(["GET", "POST"], case_sensitive=False),
    help="Override HTTP method",
)
@click.option(
    "--target-file", type=click.Path(path_type=Path), help="Write Markdown example to this file"
)
@logging_options(help_text="Log level for stdout output")
def discover_command(
    host: str,
    password: str,
    path: str,
    payload: str | None,
    method: str | None,
    target_file: Path | None,
    log_level: str,
    log_file: str | None,
) -> None:
    effective_method = method.upper() if method else ("POST" if payload else "GET")
    configure_logging(log_level, log_file)

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


__all__ = ["discover_command"]
