from __future__ import annotations

from pathlib import Path

from lib.markdown_io import write_discover_example


def test_write_discover_example_writes_markdown(tmp_path: Path) -> None:
    target = tmp_path / "docs" / "discover" / "example.md"
    result = write_discover_example(
        target,
        host="http://192.168.0.1",
        path="/goform/example",
        method="GET",
        payload={"a": 1, "b": 2},
        response={"ok": True, "nums": [1, 2, 3]},
    )

    assert result == target
    text = target.read_text()
    assert text.startswith("# Discover Example: /goform/example")
    assert "```json" in text
    # Request block contains method and payload fields serialized as JSON
    assert '"method": "GET"' in text
    assert '"payload": {' in text
    assert '"a": 1' in text and '"b": 2' in text
    # Response block serialized as JSON
    assert '"ok": true' in text


def test_write_discover_example_accepts_scalar_payload(tmp_path: Path) -> None:
    target = tmp_path / "docs" / "discover" / "example2.md"
    write_discover_example(
        target,
        host="h",
        path="/p",
        method="POST",
        payload=None,
        response=[1, 2, 3],
    )
    text = target.read_text()
    # Null payload prints as JSON null inside fenced block
    assert "\nnull\n" in text or '"payload": null' in text
    assert "```json" in text and "```" in text[-4:]
