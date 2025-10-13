"""Implementation of the `zte discover` command consolidated under commands/."""

from __future__ import annotations

import json
from pathlib import Path

import click
import httpx

from lib import markdown_io, snapshots
from lib.logging_setup import get_logger, logging_options
from lib.options import router_options

# Import the module to allow tests to monkeypatch symbols via services.zte_client
from services import zte_client


@click.command(name="discover", help="Invoke router REST endpoints and capture responses")
@router_options(default_host="http://192.168.0.1")
@click.option("--path", required=True, help="Relative endpoint path")
@click.option("--payload", help="Optional payload (JSON string)")
@click.option(
    "--method",
    type=click.Choice(["GET", "POST"], case_sensitive=False),
    help="Override HTTP method",
)
@click.option(
    "--target-file",
    type=click.Path(path_type=Path),
    help="Write Markdown example to this file",
)
@logging_options(help_text="Log level for stdout output")
def discover_command(
    router_host: str,
    router_password: str,
    path: str,
    payload: str | None,
    method: str | None,
    target_file: Path | None,
    log_level: str,
    log_file: str | None,
) -> None:
    """
    Run a discovery request against a ZTE router and emit the response or
    save a discovery example to a file.

    Sends an HTTP request to the router using the provided path and credentials.
    Prints the router response to stdout (pretty-printed JSON for object/array
    responses), or writes a Markdown discovery example and a snapshot when a
    target file is specified.

    Parameters:
        router_host: Router base URL or host used to create the client.
        router_password: Password used to authenticate with the router.
        path: Relative endpoint path to request on the router.
        payload: Optional JSON string payload to include in the request body.
            When present and no explicit method is provided, the command uses
            POST.
        method: Optional HTTP method override (e.g., "GET" or "POST"). When
            omitted, POST is used if payload is provided, otherwise GET.
        target_file: Optional path to write a Markdown discovery example. When
            provided the function writes the example, saves a snapshot, prints
            the written path, and returns.
        log_level: Logging verbosity level (affects what is logged).
        log_file: Optional file path to write logs.

    Raises:
        click.ClickException: On connection failures, authentication errors,
            timeouts, parse errors, or other client request errors.
    """
    effective_method = method.upper() if method else ("POST" if payload else "GET")
    logger = get_logger(log_level, log_file)

    logger.info(f"Starting discovery: host={router_host} path={path} method={effective_method}")
    if payload is not None and log_level.lower() == "debug":
        logger.debug(f"Payload: {payload}")

    try:
        client = zte_client.ZTEClient(router_host)
    except httpx.ConnectError as exc:
        raise click.ClickException(f"Unable to connect to router host: {exc}") from exc

    try:
        client.login(router_password)
        logger.debug(f"Logged in to {router_host}")
        response = client.request(path, method=effective_method, payload=payload, expects="json")
    except httpx.ConnectError as exc:
        raise click.ClickException("Unable to connect to router host") from exc
    except zte_client.TimeoutError as exc:
        raise click.ClickException(f"Request timed out: {exc}") from exc
    except zte_client.AuthenticationError as exc:
        raise click.ClickException(str(exc)) from exc
    except zte_client.ResponseParseError as exc:
        raise click.ClickException(f"Failed to parse router response: {exc}") from exc
    except zte_client.RequestError as exc:
        raise click.ClickException(str(exc)) from exc

    if target_file:
        target_path = target_file if target_file.is_absolute() else Path.cwd() / target_file
        markdown_io.write_discover_example(
            target_path,
            host=router_host,
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
                "host": router_host,
                "path": path,
                "method": effective_method,
                "payload": payload,
            },
            response=response,
        )
        # Keep logs simple; no additional debug context
        click.echo(str(target_path))
        return

    if isinstance(response, dict | list):
        click.echo(json.dumps(response, indent=2, sort_keys=True))
    else:
        click.echo(response)


__all__ = ["discover_command"]
