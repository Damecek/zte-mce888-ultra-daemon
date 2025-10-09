"""Reusable Click options for router host/password.

Provides a decorator to standardize ``--router-host`` and ``--router-password``
across all CLI commands.
"""

from __future__ import annotations

try:  # Import guarded to avoid hard dependency at import time
    import click
except Exception:  # pragma: no cover - defensive fallback for non-CLI contexts
    click = None  # type: ignore


def router_options(*, default_host: str = "192.168.0.1"):
    """Attach ``--router-host`` and ``--router-password`` options.

    - ``--router-host``: required, defaults to the provided ``default_host``
    - ``--router-password``: required
    """
    if click is None:  # pragma: no cover - import guard

        def passthrough(func):
            return func

        return passthrough

    def decorator(func):  # type: ignore[override]
        func = click.option(
            "router_password",
            "--router-password",
            required=True,
            help="Router admin password",
        )(func)
        func = click.option(
            "router_host",
            "--router-host",
            default=default_host,
            show_default=True,
            required=True,
            help="Router host URL",
        )(func)
        return func

    return decorator


__all__ = ["router_options"]
