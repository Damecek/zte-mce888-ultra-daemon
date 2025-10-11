"""Central logging configuration for CLI and services.

Provides a simple, structured formatter and convenience helpers that the
Click commands can use. The formatter emits a consistent, readable line
including optional context key=value pairs so important fields (e.g.,
``topic=...``) are visible in logs.
"""

from __future__ import annotations

import logging
from pathlib import Path

_CONFIGURED = False


def configure(level: int = logging.WARNING, handler: logging.Handler | None = None) -> None:
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
    """Emit simple, readable log lines.

    Output format:
      ``<ts> <LEVEL> <component>: <message>[ | error=ExcType: details]``
    """

    def format(self, record: logging.LogRecord) -> str:  # noqa: D401 - short override
        timestamp = self.formatTime(record)
        component = record.name.split(".")[-1]
        base = f"{timestamp} {record.levelname} {component}: {record.getMessage()}"

        # If an exception is attached, append a concise one-line summary so
        # operational errors (e.g., connection refused) are visible without
        # dumping multi-line tracebacks in normal runs.
        if record.exc_info:
            exc_type, exc_value, _ = record.exc_info
            if exc_type is not None and exc_value is not None:
                base += f" | error={exc_type.__name__}: {exc_value}"
        return base


_LEVEL_ALIASES: dict[str, int] = {
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "warn": logging.WARNING,
    "error": logging.ERROR,
}


def get_logger(level: str = "warn", log_file: str | Path | None = None) -> logging.Logger:
    """Configure application-wide structured logging and return the logger.

    Compatible wrapper kept for commands migrated from the legacy package.
    """
    resolved_level = _LEVEL_ALIASES.get(level.lower(), logging.WARNING)
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

    # Tame noisy third-party libraries based on desired verbosity.
    for name in ("httpx", "httpcore", "urllib3"):
        ext_logger = logging.getLogger(name)
        ext_logger.setLevel(resolved_level)
        # Allow these to propagate to root handlers if present
        # so basicConfig formatting applies, but level gates noise.
        ext_logger.propagate = True

    # Also align the root logger level with the chosen app level
    # while keeping its default handlers/formatting from basicConfig.
    root_logger = logging.getLogger()
    root_logger.setLevel(resolved_level)

    return logger


__all__ = ["configure", "get_logger", "StructuredFormatter"]


# Click integration helpers
try:  # Import guarded to avoid hard dependency at import time
    import click
except ImportError:  # pragma: no cover - defensive fallback for non-CLI contexts
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
            default="warn",
            show_default=True,
            help=help_text,
        )(func)
        return func

    return decorator


__all__.append("logging_options")
