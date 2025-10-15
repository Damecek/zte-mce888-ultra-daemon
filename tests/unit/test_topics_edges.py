from __future__ import annotations

import pytest

from lib import topics


def test_normalize_topic_rejects_empty_values() -> None:
    # Completely empty string
    with pytest.raises(ValueError):
        topics.normalize_topic("")
    # Only slashes and whitespace collapse to empty
    with pytest.raises(ValueError):
        topics.normalize_topic(" /  /  / ")


def test_build_request_topic_normalization_and_validation() -> None:
    # Normalization of root with backslashes and spaces plus metric trimming
    assert topics.build_request_topic("  ZTE\\Home  ", "  Provider  ") == "zte/home/provider/get"

    # Invalid root collapses to empty -> error from normalize_topic
    with pytest.raises(ValueError):
        topics.build_request_topic(" / / ", "metric")

    # Empty/whitespace metric -> error from _normalize_segment
    with pytest.raises(ValueError):
        topics.build_request_topic("root", "")
    with pytest.raises(ValueError):
        topics.build_request_topic("root", "  ")


def test_build_response_topic_nested_and_invalid_parts() -> None:
    # Backslashes in root and dot-path metric are normalized
    assert topics.build_response_topic(" ZTE\\Home ", " LTE.RSRP1 ") == "zte/home/lte/rsrp1"

    # Empty segment in dotted metric (e.g., 'lte..rsrp1') -> invalid
    with pytest.raises(ValueError):
        topics.build_response_topic("zte", "lte..rsrp1")

    # Entire metric empty/whitespace -> invalid
    with pytest.raises(ValueError):
        topics.build_response_topic("zte", "")
    with pytest.raises(ValueError):
        topics.build_response_topic("zte", "   ")


def test_parse_request_topic_for_root_rejects_non_get_and_mismatch() -> None:
    # Topic not ending with /get
    with pytest.raises(ValueError):
        topics.parse_request_topic_for_root("home/zte/lte/set", "home/zte")

    # Root prefix mismatch
    with pytest.raises(ValueError):
        topics.parse_request_topic_for_root("other/zte/lte/get", "home/zte")


def test_response_topic_from_request_rejects_unsupported() -> None:
    # Missing trailing /get -> unsupported request
    with pytest.raises(ValueError):
        topics.response_topic_from_request("home/zte/lte")
