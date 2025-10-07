from pathlib import Path


REQUIRED_SECTIONS = [
    "LTE Metrics",
    "NR5G Metrics",
    "Provider",
    "Cell",
    "Neighbor Cells",
    "Connection State",
    "Bands",
    "WAN IP",
    "Temperatures",
]


def test_metrics_document_lists_required_sections():
    metrics_doc = Path("docs/metrics.md")
    assert metrics_doc.exists(), "docs/metrics.md must exist"

    contents = metrics_doc.read_text().lower()
    missing = [section for section in REQUIRED_SECTIONS if section.lower() not in contents]

    assert not missing, f"Missing sections in docs/metrics.md: {missing}"
