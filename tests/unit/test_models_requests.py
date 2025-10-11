import pytest

from models.metric_request import MetricRequest


def test_metric_request_from_topic_handles_single_metric() -> None:
    request = MetricRequest.from_topic("ZTE/Provider/GET")

    assert request.topic == "zte/provider/get"
    assert request.root == "zte"
    assert request.metric == "provider"
    assert request.is_aggregate is False


def test_metric_request_from_topic_handles_aggregate() -> None:
    request = MetricRequest.from_topic("zte/lte/get")

    assert request.topic == "zte/lte/get"
    assert request.root == "zte"
    assert request.metric == "lte"
    assert request.is_aggregate is True


def test_metric_request_requires_get_suffix() -> None:
    with pytest.raises(ValueError):
        MetricRequest.from_topic("zte/provider")
