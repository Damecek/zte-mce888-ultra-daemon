"""Ensure metrics documentation enumerates all required fields."""

from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture()
def metrics_doc() -> str:
    """
    Load the metrics documentation from docs/metrics.md.
    
    Returns:
        str: The contents of docs/metrics.md decoded using UTF-8.
    """
    return Path("docs/metrics.md").read_text(encoding="utf-8")


def test_metrics_documentation_lists_all_sections(metrics_doc: str) -> None:
    """
    Verify that the metrics documentation contains all required metric fields.
    
    Parameters:
        metrics_doc (str): Contents of the metrics documentation (docs/metrics.md) to be checked.
    
    Notes:
        Confirms presence of the following fields: "rsrp1", "sinr1", "nr5g", "provider", "neighbors", "bands", "wan_ip", and "temp (A/M/P)".
    """
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