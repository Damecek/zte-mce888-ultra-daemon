"""Implementation of the `zte discover` command consolidated under commands/.

This module intentionally references symbols from `cli.zte` so tests that
monkeypatch `cli.zte.ZTEClient` or `cli.zte.markdown_io` continue to work.
"""

from __future__ import annotations

import json
from pathlib import Path

import click
import httpx

# Keep references via the root CLI module for test monkeypatching
from cli import zte as cli_module


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
def discover_command(
    host: str,
    password: str,
    path: str,
    payload: str | None,
    method: str | None,
    target_file: Path | None,
) -> None:
    effective_method = method.upper() if method else ("POST" if payload else "GET")

    try:
        client = cli_module.ZTEClient(host)
    except httpx.ConnectError as exc:  # pragma: no cover - defensive: instantiation may not raise
        raise click.ClickException(f"Unable to connect to modem host: {exc}") from exc

    try:
        client.login(password)
        response = client.request(path, method=effective_method, payload=payload, expects="json")
    except httpx.ConnectError as exc:
        raise click.ClickException("Unable to connect to modem host") from exc
    except cli_module.TimeoutError as exc:
        raise click.ClickException(f"Request timed out: {exc}") from exc
    except cli_module.AuthenticationError as exc:
        raise click.ClickException(str(exc)) from exc
    except cli_module.ResponseParseError as exc:
        raise click.ClickException(f"Failed to parse modem response: {exc}") from exc
    except cli_module.RequestError as exc:
        raise click.ClickException(str(exc)) from exc

    if target_file:
        target_path = target_file if target_file.is_absolute() else Path.cwd() / target_file
        cli_module.markdown_io.write_discover_example(
            target_path,
            host=host,
            path=path,
            method=effective_method,
            payload=payload,
            response=response,
        )
        cli_module.snapshots.save_snapshot(
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

