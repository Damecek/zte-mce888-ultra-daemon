"""Logging helpers for the hello-world daemon."""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict

LEVEL_ALIASES: Dict[str, int] = {
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "warn": logging.WARNING,
    "warning": logging.WARNING,
    "error": logging.ERROR,
}


class StructuredFormatter(logging.Formatter):
    """Emit structured JSON log lines."""

    def format(self, record: logging.LogRecord) -> str:  # noqa: D401 - short override
        payload: Dict[str, Any] = {
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
        return json.dumps(payload, ensure_ascii=False)


def configure_logging(level: str = "info", log_file: str | Path | None = None) -> logging.Logger:
    """Configure application-wide logging."""
    resolved_level = LEVEL_ALIASES.get(level.lower(), logging.INFO)
    logger = logging.getLogger("zte_daemon")
    logger.setLevel(resolved_level)

    # Remove any existing handlers to avoid duplicate lines across invocations
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
