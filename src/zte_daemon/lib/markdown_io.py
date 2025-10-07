"""Markdown utilities for documenting modem discoveries."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

__all__ = ["write_discover_example"]


def _to_json_block(data: Any) -> str:
    if data is None:
        return "null"
    return json.dumps(data, indent=2, ensure_ascii=False, sort_keys=True)


def write_discover_example(
    target_file: str | Path,
    *,
    host: str,
    path: str,
    method: str,
    payload: Any | None,
    response: Any,
) -> Path:
    """Render a Markdown file capturing the request/response exchange."""

    output_path = Path(target_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    payload_block = _to_json_block(payload)
    response_block = _to_json_block(response)

    content = "\n".join(
        [
            "# ZTE Discover Example",
            "",
            "## Request",
            f"Host: {host}",
            f"Path: {path}",
            f"Method: {method.upper()}",
            "",
            "```json",
            payload_block,
            "```",
            "",
            "## Response",
            "```json",
            response_block,
            "```",
            "",
        ]
    )

    output_path.write_text(content, encoding="utf-8")
    return output_path
