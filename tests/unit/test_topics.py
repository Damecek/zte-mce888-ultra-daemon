import pytest

from lib import topics


def test_normalize_topic_strips_whitespace_and_lowercases() -> None:
    assert topics.normalize_topic("  ZTE/Provider/GET  ") == "zte/provider/get"
    assert topics.normalize_topic("lte//signal") == "lte/signal"


def test_build_request_and_response_topics_support_subpaths() -> None:
    assert topics.build_request_topic("zte/home", "provider") == "zte/home/provider/get"
    assert topics.build_response_topic("zte/home", "provider") == "zte/home/provider"


def test_build_response_topic_translates_nested_metric_identifier() -> None:
    # Dot in metric identifier becomes a path segment in response topic
    assert topics.build_response_topic("zte", "lte.rsrp1") == "zte/lte/rsrp1"


def test_parse_request_topic_returns_metadata() -> None:
    parsed = topics.parse_request_topic("ZTE/LTE/get")
    assert parsed.request_topic == "zte/lte/get"
    assert parsed.root == "zte"
    assert parsed.metric == "lte"
    assert parsed.is_aggregate is True


def test_parse_request_topic_for_root_supports_nested_metrics() -> None:
    parsed = topics.parse_request_topic_for_root("ZTE/LTE/RSRP1/GET", "zte")
    assert parsed.request_topic == "zte/lte/rsrp1/get"
    assert parsed.root == "zte"
    assert parsed.metric == "lte.rsrp1"
    assert parsed.is_aggregate is False


def test_response_topic_from_request() -> None:
    assert topics.response_topic_from_request("zte/provider/get") == "zte/provider"


def test_parse_request_topic_rejects_invalid_shapes() -> None:
    with pytest.raises(ValueError):
        topics.parse_request_topic("zte/provider")
    with pytest.raises(ValueError):
        topics.parse_request_topic("lte/get")
