"""Ensure metrics documentation enumerates all required fields."""

from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture()
def metrics_doc() -> str:
    return Path("docs/metrics.md").read_text(encoding="utf-8")


def test_metrics_documentation_lists_all_sections(metrics_doc: str) -> None:
    expected_keywords = [
        "rsrp1",
        "sinr1",
        "nr5g",
        "provider",
        "neighbors",
        "bands",
        "wan_ip",
        "temp (A/M/P)",
    ]

    for keyword in expected_keywords:
        assert keyword in metrics_doc
