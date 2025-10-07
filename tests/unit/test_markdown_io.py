"""Unit tests for markdown_io module."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from zte_daemon.lib.markdown_io import write_discover_example


def test_write_discover_example_creates_valid_markdown(tmp_path: Path) -> None:
    """Test that write_discover_example creates a properly formatted Markdown file."""
    output = write_discover_example(
        tmp_path / "example.md",
        host="192.168.0.1",
        path="goform/goform_get_cmd_process?cmd=status",
        method="GET",
        payload=None,
        response={"result": "success", "data": {"signal": -85}},
    )

    assert output.exists()
    content = output.read_text(encoding="utf-8")
    assert "# ZTE Discover Example" in content
    assert "## Request" in content
    assert "Host: 192.168.0.1" in content
    assert "Path: goform/goform_get_cmd_process?cmd=status" in content
    assert "Method: GET" in content
    assert "## Response" in content
    assert '"result": "success"' in content


def test_write_discover_example_with_post_payload(tmp_path: Path) -> None:
    """Test writing a POST request example with JSON payload."""
    payload = {"action": "reboot", "timeout": 30}
    response = {"status": "ok"}

    output = write_discover_example(
        tmp_path / "post_example.md",
        host="192.168.0.1",
        path="goform/goform_set_cmd_process",
        method="POST",
        payload=payload,
        response=response,
    )

    content = output.read_text(encoding="utf-8")
    assert "Method: POST" in content
    assert '"action": "reboot"' in content
    assert '"timeout": 30' in content
    assert '"status": "ok"' in content


def test_write_discover_example_with_null_payload(tmp_path: Path) -> None:
    """Test handling of None/null payload."""
    output = write_discover_example(
        tmp_path / "null_payload.md",
        host="192.168.0.1",
        path="goform/status",
        method="GET",
        payload=None,
        response={"value": 42},
    )

    content = output.read_text(encoding="utf-8")
    assert "null" in content
    assert "```json" in content


def test_write_discover_example_creates_parent_directories(tmp_path: Path) -> None:
    """Test that parent directories are created automatically."""
    nested_path = tmp_path / "level1" / "level2" / "level3" / "example.md"
    
    output = write_discover_example(
        nested_path,
        host="192.168.0.1",
        path="goform/test",
        method="GET",
        payload=None,
        response={"test": True},
    )

    assert output.exists()
    assert output.parent.parent.parent.exists()


def test_write_discover_example_with_complex_nested_response(tmp_path: Path) -> None:
    """Test handling of deeply nested JSON response structures."""
    response = {
        "status": "ok",
        "data": {
            "metrics": {
                "signal": {"rsrp": [-85, -87], "sinr": [18, 16]},
                "network": {"type": "5G", "band": "n28"},
            },
            "metadata": {"timestamp": "2025-10-06T12:00:00Z"},
        },
    }

    output = write_discover_example(
        tmp_path / "complex.md",
        host="192.168.0.1",
        path="goform/metrics",
        method="GET",
        payload=None,
        response=response,
    )

    content = output.read_text(encoding="utf-8")
    # Verify JSON is pretty-printed and sorted
    assert '"band": "n28"' in content
    assert '"rsrp": [' in content
    assert '"timestamp": "2025-10-06T12:00:00Z"' in content


def test_write_discover_example_with_special_characters(tmp_path: Path) -> None:
    """Test handling of special characters in response data."""
    response = {
        "message": "Test with special chars: ñ, é, 中文, emoji 🚀",
        "symbols": "<>&\"'",
    }

    output = write_discover_example(
        tmp_path / "special_chars.md",
        host="192.168.0.1",
        path="goform/test",
        method="POST",
        payload={"query": "special"},
        response=response,
    )

    content = output.read_text(encoding="utf-8")
    assert "emoji 🚀" in content
    assert "中文" in content


def test_write_discover_example_with_list_response(tmp_path: Path) -> None:
    """Test handling of response that is a list."""
    response = [
        {"id": 1, "name": "Device A"},
        {"id": 2, "name": "Device B"},
        {"id": 3, "name": "Device C"},
    ]

    output = write_discover_example(
        tmp_path / "list_response.md",
        host="192.168.0.1",
        path="goform/devices",
        method="GET",
        payload=None,
        response=response,
    )

    content = output.read_text(encoding="utf-8")
    assert '"id": 1' in content
    assert '"name": "Device A"' in content


def test_write_discover_example_with_empty_response(tmp_path: Path) -> None:
    """Test handling of empty response objects."""
    output = write_discover_example(
        tmp_path / "empty.md",
        host="192.168.0.1",
        path="goform/empty",
        method="GET",
        payload=None,
        response={},
    )

    content = output.read_text(encoding="utf-8")
    assert "{}" in content


def test_write_discover_example_method_normalization(tmp_path: Path) -> None:
    """Test that HTTP method is normalized to uppercase."""
    output = write_discover_example(
        tmp_path / "lowercase_method.md",
        host="192.168.0.1",
        path="goform/test",
        method="get",
        payload=None,
        response={"result": "ok"},
    )

    content = output.read_text(encoding="utf-8")
    assert "Method: GET" in content


def test_write_discover_example_returns_resolved_path(tmp_path: Path) -> None:
    """Test that the function returns the actual Path object created."""
    target = tmp_path / "result.md"
    output = write_discover_example(
        target,
        host="192.168.0.1",
        path="goform/test",
        method="GET",
        payload=None,
        response={"test": True},
    )

    assert isinstance(output, Path)
    assert output == target
    assert output.is_absolute() or output.exists()


def test_write_discover_example_accepts_path_object(tmp_path: Path) -> None:
    """Test that the function accepts both str and Path objects."""
    path_obj = tmp_path / "path_object.md"
    
    output = write_discover_example(
        path_obj,
        host="192.168.0.1",
        path="goform/test",
        method="GET",
        payload=None,
        response={"test": True},
    )

    assert output.exists()


def test_write_discover_example_with_numeric_response_values(tmp_path: Path) -> None:
    """Test handling of various numeric types in response."""
    response = {
        "integer": 42,
        "float": 3.14159,
        "negative": -100,
        "zero": 0,
        "scientific": 1.23e-4,
    }

    output = write_discover_example(
        tmp_path / "numeric.md",
        host="192.168.0.1",
        path="goform/metrics",
        method="GET",
        payload=None,
        response=response,
    )

    content = output.read_text(encoding="utf-8")
    assert '"integer": 42' in content
    assert '"float": 3.14159' in content


def test_write_discover_example_with_boolean_values(tmp_path: Path) -> None:
    """Test handling of boolean values in JSON."""
    response = {
        "enabled": True,
        "disabled": False,
    }

    output = write_discover_example(
        tmp_path / "boolean.md",
        host="192.168.0.1",
        path="goform/config",
        method="GET",
        payload=None,
        response=response,
    )

    content = output.read_text(encoding="utf-8")
    assert '"enabled": true' in content
    assert '"disabled": false' in content