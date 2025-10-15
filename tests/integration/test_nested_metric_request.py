from __future__ import annotations

from dataclasses import dataclass

import pytest

from models.daemon_state import DaemonState
from models.mqtt_config import MQTTConfig
from pipeline.dispatcher import Dispatcher


@dataclass
class StubMetricReader:
    responses: dict[str, object]

    def __post_init__(self) -> None:
        self.calls: list[str] = []

    def fetch(self, metric: str) -> object:
        self.calls.append(metric)
        if metric not in self.responses:
            raise KeyError(metric)
        return self.responses[metric]


@dataclass
class StubAggregator:
    def __post_init__(self) -> None:
        self.calls = 0

    def collect_lte(self) -> dict[str, object]:
        self.calls += 1
        return {"rsrp1": -92.0}


class StubMQTTClient:
    def __init__(self) -> None:
        self.publishes: list[object] = []

    def publish(self, envelope: object) -> None:
        self.publishes.append(envelope)


@pytest.fixture()
def dispatcher_setup() -> tuple[Dispatcher, StubMetricReader, StubAggregator, StubMQTTClient]:
    metric_reader = StubMetricReader({"lte.rsrp1": -95})
    aggregator = StubAggregator()
    mqtt_client = StubMQTTClient()
    state = DaemonState()
    config = MQTTConfig(host="mqtt.local")
    dispatcher = Dispatcher(
        mqtt_config=config,
        metric_reader=metric_reader,
        aggregator=aggregator,
        mqtt_client=mqtt_client,
        state=state,
    )
    return dispatcher, metric_reader, aggregator, mqtt_client


def test_nested_metric_request_translates_and_publishes(
    dispatcher_setup: tuple[Dispatcher, StubMetricReader, StubAggregator, StubMQTTClient],
) -> None:
    dispatcher, metric_reader, aggregator, mqtt_client = dispatcher_setup

    dispatcher.handle_request("zte/lte/rsrp1/get")

    assert metric_reader.calls == ["lte.rsrp1"]
    assert aggregator.calls == 0
    assert mqtt_client.publishes, "publish should have been invoked"

    envelope = mqtt_client.publishes[0]
    assert envelope.topic == "zte/lte/rsrp1"
    assert envelope.payload == -95
