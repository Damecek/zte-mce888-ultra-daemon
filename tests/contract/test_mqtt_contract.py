from lib import topics
from models.metric_request import MetricRequest
from models.publish_envelope import PublishEnvelope


def test_request_and_response_topics_are_lowercased() -> None:
    request_topic = topics.build_request_topic("ZTE", "Provider")
    response_topic = topics.build_response_topic("ZTE", "Provider")

    assert request_topic == "zte/provider/get"
    assert response_topic == "zte/provider"

    parsed = topics.parse_request_topic("ZTE/Provider/GET")
    assert parsed.root == "zte"
    assert parsed.metric == "provider"
    assert parsed.is_aggregate is False


def test_metric_request_normalizes_and_detects_aggregate() -> None:
    single = MetricRequest.from_topic("ZTE/Provider/GET")
    assert single.topic == "zte/provider/get"
    assert single.root == "zte"
    assert single.metric == "provider"
    assert single.is_aggregate is False

    aggregate = MetricRequest.from_topic("ZTE/LTE/get")
    assert aggregate.topic == "zte/lte/get"
    assert aggregate.root == "zte"
    assert aggregate.metric == "lte"
    assert aggregate.is_aggregate is True


def test_publish_envelope_enforces_qos_and_retain_contract() -> None:
    scalar = PublishEnvelope(topic="ZTE/Provider", payload="O2")
    assert scalar.topic == "zte/provider"
    assert scalar.payload == "O2"
    assert scalar.qos == 0
    assert scalar.retain is False

    aggregate_payload = {"rsrp1": -92.0, "sinr1": 12.5}
    aggregate = PublishEnvelope(topic="ZTE/LTE", payload=aggregate_payload)
    assert aggregate.topic == "zte/lte"
    assert aggregate.payload == aggregate_payload
    assert aggregate.qos == 0
    assert aggregate.retain is False
    assert isinstance(aggregate.payload, dict)
