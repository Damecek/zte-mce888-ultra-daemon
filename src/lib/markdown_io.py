"""Helpers for writing discovery Markdown artifacts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _format_payload(payload: Any) -> str:
    """
    Format a payload value into a human-readable string suitable for inclusion in discovery artifacts.
    
    Parameters:
        payload (Any): The value to format. If `payload` is None, it is represented as the literal string `"null"`. If `payload` is a `dict` or `list`, it is serialized as pretty-printed JSON with 2-space indentation and keys sorted. Otherwise the value's `str()` representation is returned.
    
    Returns:
        str: The formatted string representation of `payload`.
    """
    if payload is None:
        return "null"
    if isinstance(payload, dict | list):
        return json.dumps(payload, indent=2, sort_keys=True)
    return str(payload)


def _format_response(response: Any) -> str:
    """
    Format a response value for inclusion in discovery Markdown.
    
    Parameters:
        response (Any): The value to format; typically a dict, list, or other serializable value.
    
    Returns:
        str: Pretty-printed JSON (2-space indent, keys sorted) if `response` is a dict or list, otherwise `str(response)`.
    """
    if isinstance(response, dict | list):
        return json.dumps(response, indent=2, sort_keys=True)
    return str(response)


def write_discover_example(
    target_file: Path | str,
    *,
    host: str,
    path: str,
    method: str,
    payload: Any,
    response: Any,
) -> Path:
    target_path = Path(target_file)
    target_path.parent.mkdir(parents=True, exist_ok=True)

    request_block = _format_payload({
        "host": host,
        "path": path,
        "method": method,
        "payload": payload,
    })

    response_block = _format_response(response)

    contents = (
        f"# Discover Example: {path}\n\n"
        "## Request\n"
        "```json\n"
        f"{request_block}\n"
        "```\n\n"
        "## Response\n"
        "```json\n"
        f"{response_block}\n"
        "```\n"
    )

    target_path.write_text(contents)
    return target_path


__all__ = ["write_discover_example"]