from __future__ import annotations

from typing import Any


def coerce_number_like(value: Any) -> Any:
    """
    Convert number-like strings to int/float, otherwise return value unchanged.

    - Trims whitespace for strings; empty strings are returned as-is.
    - If a trimmed string contains a dot, returns float; otherwise tries int.
    - On conversion failure returns the trimmed string.
    - Non-string inputs are returned unchanged.
    """
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return text
        try:
            if "." in text:
                return float(text)
            return int(text)
        except ValueError:
            return text
    return value


__all__ = ["coerce_number_like"]
