"""CLI command for exploring ZTE modem REST endpoints."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import click
import httpx

from zte_daemon.lib.markdown_io import write_discover_example
from zte_daemon.lib.snapshots import write_snapshot
from zte_daemon.logging.config import configure_logging
from zte_daemon.modem.zte_client import AuthenticationError, RequestError, ZTEClient

_HTTP_METHODS = ["GET", "POST"]


@click.command(name="discover", help="Discover modem REST endpoints and capture responses.")
@click.option("host", "--host", required=True, help="Modem host or IP address (e.g., 192.168.0.1).")
@click.option(
    "password",
    "--password",
    required=True,
    help="Password used for modem REST authentication.",
)
@click.option(
    "endpoint",
    "--path",
    required=True,
    help="Relative REST path to query (e.g., goform/goform_get_cmd_process?cmd=...).",
)
@click.option(
    "payload",
    "--payload",
    help="Optional JSON payload to send with the request.",
)
@click.option(
    "method",
    "--method",
    type=click.Choice(_HTTP_METHODS, case_sensitive=False),
    help="Explicit HTTP method override.",
)
@click.option(
    "target_file",
    "--target-file",
    type=click.Path(path_type=str),
    help="Write Markdown example to this path (under docs/discover/).",
)
@click.option(
    "expects",
    "--expects",
    type=click.Choice(["json", "text"], case_sensitive=False),
    default="json",
    show_default=True,
    help="Expected response type.",
)
@click.option(
    "timeout",
    "--timeout",
    type=float,
    default=10.0,
    show_default=True,
    help="HTTP timeout in seconds.",
)
@click.option(
    "log_level",
    "--log",
    type=click.Choice(["debug", "info", "warn", "error"], case_sensitive=False),
    default="info",
    show_default=True,
    help="Log level for stdout and optional file handlers.",
)
@click.option(
    "log_file",
    "--log-file",
    type=click.Path(path_type=str),
    help="Optional log file destination.",
)
def discover_command(
    *,
    host: str,
    password: str,
    endpoint: str,
    payload: str | None,
    method: str | None,
    target_file: str | None,
    expects: str,
    timeout: float,
    log_level: str,
    log_file: str | None,
) -> None:
    """Execute a discover request against the modem REST API."""

    logger = configure_logging(log_level, log_file)

    http_method = method.upper() if method else ("POST" if payload else "GET")
    json_payload: Any | None = None

    if payload:
        try:
            json_payload = json.loads(payload)
        except json.JSONDecodeError as exc:  # pragma: no cover - validated via contract tests
            raise click.ClickException(f"Invalid JSON payload: {exc}") from exc

    try:
        with ZTEClient(host, timeout=timeout) as client:
            client.login(password)
            response = client.request(
                endpoint,
                method=http_method,
                payload=json_payload,
                expects=expects.lower(),
            )
    except AuthenticationError as exc:
        raise click.ClickException("Authentication failed: verify modem credentials.") from exc
    except RequestError as exc:
        cause = exc.__cause__
        if isinstance(cause, httpx.ConnectError):
            raise click.ClickException(f"Unable to reach modem at {host}.") from exc
        raise click.ClickException(str(exc)) from exc

    pretty_output: str
    if expects.lower() == "json" and isinstance(response, (dict, list)):
        pretty_output = json.dumps(response, indent=2, sort_keys=True)
    else:
        pretty_output = str(response)

    click.echo(pretty_output)
    logger.info(
        "Completed discover request",
        extra={
            "component": "CLI",
            "context": {"host": host, "path": endpoint, "method": http_method},
        },
    )

    if target_file:
        output_path = write_discover_example(
            target_file,
            host=host,
            path=endpoint,
            method=http_method,
            payload=json_payload,
            response=response,
        )
        write_snapshot(
            response,
            Path(target_file).with_suffix(".json"),
            metadata={
                "host": host,
                "path": endpoint,
                "method": http_method,
                "expects": expects.lower(),
                "payload": json_payload,
            },
        )
        click.echo(str(Path(output_path).resolve()))
