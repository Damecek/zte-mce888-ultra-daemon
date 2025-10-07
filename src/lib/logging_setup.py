"""Central logging configuration for CLI and services."""
from __future__ import annotations

import logging
from typing import Optional

_CONFIGURED = False


def configure(level: int = logging.INFO, handler: Optional[logging.Handler] = None) -> None:
    global _CONFIGURED
    if _CONFIGURED:
        return

    logging.basicConfig(
        level=level,
        handlers=[handler] if handler else None,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    _CONFIGURED = True


__all__ = ["configure"]
