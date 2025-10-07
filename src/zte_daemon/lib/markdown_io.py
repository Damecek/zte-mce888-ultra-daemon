"""Markdown utilities for documenting modem discoveries."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

__all__ = ["write_discover_example"]


def _to_json_block(data: Any) -> str:
    """
    Convert Python data to a JSON-formatted string suitable for embedding in Markdown code blocks.
    
    Parameters:
        data (Any): The value to serialize. If `None`, the function returns the literal string "null".
    
    Returns:
        json_block (str): A JSON-formatted string with an indentation of 2 spaces, Unicode characters preserved, and keys sorted; or the string "null" when `data` is `None`.
    """
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
    """
    Render a Markdown file that documents a single request/response exchange and write it to the given target path.
    
    The function serializes `payload` and `response` to JSON-formatted blocks (uses the string "null" when `payload` or `response` is None), assembles a Markdown document with Request and Response sections (the HTTP method is uppercased), writes the document to `target_file`, and returns the written path.
    
    Parameters:
        target_file (str | Path): Destination file path for the generated Markdown. Parent directories will be created if needed.
        host (str): Request host to include in the document.
        path (str): Request path to include in the document.
        method (str): HTTP method for the request (will be uppercased in output).
        payload (Any | None): Request payload to include; serialized to a JSON block or "null" if None.
        response (Any): Response data to include; serialized to a JSON block.
    
    Returns:
        Path: The path to the written Markdown file.
    """

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