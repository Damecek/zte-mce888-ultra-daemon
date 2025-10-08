"""Implementation of the `zte discover` command consolidated under commands/."""

from __future__ import annotations

import json
from pathlib import Path

import click
import httpx

from lib import markdown_io, snapshots
from lib.logging_setup import get_logger, logging_options
# Import the module to allow tests to monkeypatch symbols via services.zte_client
from services import zte_client


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
    logger = get_logger(log_level, log_file)

    logger.info(f"Starting discovery: host={host} path={path} method={effective_method}")
    if payload is not None and log_level.lower() == "debug":
        logger.debug(f"Payload: {payload}")

    try:
        client = zte_client.ZTEClient(host)
    except httpx.ConnectError as exc:
        raise click.ClickException(f"Unable to connect to modem host: {exc}") from exc

    try:
        client.login(password)
        logger.debug(f"Logged in to {host}")
        response = client.request(path, method=effective_method, payload=payload, expects="json")
    except httpx.ConnectError as exc:
        raise click.ClickException("Unable to connect to modem host") from exc
    except zte_client.TimeoutError as exc:
        raise click.ClickException(f"Request timed out: {exc}") from exc
    except zte_client.AuthenticationError as exc:
        raise click.ClickException(str(exc)) from exc
    except zte_client.ResponseParseError as exc:
        raise click.ClickException(f"Failed to parse modem response: {exc}") from exc
    except zte_client.RequestError as exc:
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
        logger.info(f"Wrote discovery example: {target_path}")
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
        # Keep logs simple; no additional debug context
        click.echo(str(target_path))
        return

    if isinstance(response, (dict, list)):
        click.echo(json.dumps(response, indent=2, sort_keys=True))
    else:
        click.echo(response)


__all__ = ["discover_command"]
