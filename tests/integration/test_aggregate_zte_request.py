from __future__ import annotations

from dataclasses import dataclass

import pytest

from models.daemon_state import DaemonState
from models.mqtt_config import MQTTConfig
from pipeline.dispatcher import Dispatcher


@dataclass
class StubMetricReader:
    def __post_init__(self) -> None:
        self.calls: list[str] = []

    def fetch(self, metric: str) -> object:  # pragma: no cover - not used here
        self.calls.append(metric)
        raise KeyError(metric)


@dataclass
class StubAggregator:
    def __post_init__(self) -> None:
        self.lte_calls = 0
        self.all_calls = 0

    def collect_lte(self) -> dict[str, object]:
        self.lte_calls += 1
        return {"rsrp1": -90}

    def collect_all(self) -> dict[str, object]:
        self.all_calls += 1
        return {
            "provider": "Vodafone",
            "cell": "abcd",
            "connection": "ENDC",
            "bands": "B20 + n28",
            "wan_ip": "10.0.0.2",
            "lte": {"rsrp1": -90},
            "nr5g": {"pci": 123},
            "temp": {"a": 40},
        }


class StubMQTTClient:
    def __init__(self) -> None:
        self.publishes: list[object] = []

    def publish(self, envelope: object) -> None:
        self.publishes.append(envelope)


@pytest.fixture()
def dispatcher_setup() -> tuple[Dispatcher, StubMetricReader, StubAggregator, StubMQTTClient]:
    metric_reader = StubMetricReader()
    aggregator = StubAggregator()
    mqtt_client = StubMQTTClient()
    state = DaemonState()
    # Configured root includes '/zte'
    config = MQTTConfig(host="mqtt.local", root_topic="home/zte")
    dispatcher = Dispatcher(
        mqtt_config=config,
        metric_reader=metric_reader,
        aggregator=aggregator,
        mqtt_client=mqtt_client,
        state=state,
    )
    return dispatcher, metric_reader, aggregator, mqtt_client


def test_top_level_aggregate_request_publishes_nested_object(
    dispatcher_setup: tuple[Dispatcher, StubMetricReader, StubAggregator, StubMQTTClient],
) -> None:
    dispatcher, metric_reader, aggregator, mqtt_client = dispatcher_setup

    dispatcher.handle_request("home/zte/get")

    assert aggregator.all_calls == 1
    assert aggregator.lte_calls == 0
    assert mqtt_client.publishes, "aggregate publish expected"

    envelope = mqtt_client.publishes[0]
    assert envelope.topic == "home/zte/zte"
    assert isinstance(envelope.payload, dict)
    assert "lte" in envelope.payload and "nr5g" in envelope.payload
