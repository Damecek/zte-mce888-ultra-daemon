"""Central logging configuration for CLI and services.

Adds a structured JSON logger compatible with the prior
`zte_daemon.logging.config.configure_logging` API while preserving the
simple `configure()` helper already used by the new code.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

_CONFIGURED = False


def configure(level: int = logging.INFO, handler: logging.Handler | None = None) -> None:
    global _CONFIGURED
    if _CONFIGURED:
        return

    logging.basicConfig(
        level=level,
        handlers=[handler] if handler else None,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    _CONFIGURED = True


class StructuredFormatter(logging.Formatter):
    """Emit structured JSON log lines."""

    def format(self, record: logging.LogRecord) -> str:  # noqa: D401 - short override
        payload: dict[str, Any] = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "component": getattr(record, "component", "CLI"),
            "message": record.getMessage(),
        }
        if record.args and isinstance(record.args, dict):
            payload["context"] = record.args
        elif hasattr(record, "context"):
            context = getattr(record, "context")
            if isinstance(context, dict):
                payload["context"] = context
        return f"{payload.get('timestamp')} {payload.get('level')} {payload.get('component')}: {payload.get('message')}"


_LEVEL_ALIASES: dict[str, int] = {
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "warn": logging.WARNING,
    "error": logging.ERROR,
}


def get_logger(level: str = "info", log_file: str | Path | None = None) -> logging.Logger:
    """Configure application-wide structured logging and return the logger.

    Compatible wrapper kept for commands migrated from the legacy package.
    """
    resolved_level = _LEVEL_ALIASES.get(level.lower(), logging.INFO)
    logger = logging.getLogger("zte_daemon")
    logger.setLevel(resolved_level)

    # Ensure idempotency across invocations
    if logger.handlers:
        for handler in list(logger.handlers):
            logger.removeHandler(handler)

    formatter = StructuredFormatter()

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    stream_handler.setLevel(resolved_level)
    logger.addHandler(stream_handler)

    if log_file:
        path = Path(log_file)
        path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(path, encoding="utf-8")
        file_handler.setFormatter(formatter)
        file_handler.setLevel(resolved_level)
        logger.addHandler(file_handler)

    logger.propagate = False
    return logger


__all__ = ["configure", "get_logger", "StructuredFormatter"]


# Click integration helpers
try:  # Import guarded to avoid hard dependency at import time
    import click
except Exception:  # pragma: no cover - defensive fallback for non-CLI contexts
    click = None  # type: ignore


def logging_options(*, help_text: str = "Log level for stdout and file handlers"):
    """Reusable Click options for ``--log`` and ``--log-file``.

    Apply as a decorator above ``@click.command`` or directly above the command function.
    Example:

        @click.command()
        @logging_options(help_text="Log level for stdout output")
        def cmd(log_level, log_file): ...
    """
    if click is None:  # pragma: no cover - import guard

        def passthrough(func):
            return func

        return passthrough

    def decorator(func):  # type: ignore[override]
        func = click.option(
            "log_file",
            "--log-file",
            type=click.Path(path_type=str),
            help="Optional log file destination (ensures parent dir exists).",
        )(func)
        func = click.option(
            "log_level",
            "--log",
            type=click.Choice(["debug", "info", "warn", "error"], case_sensitive=False),
            default="info",
            show_default=True,
            help=help_text,
        )(func)
        return func

    return decorator


__all__.append("logging_options")
