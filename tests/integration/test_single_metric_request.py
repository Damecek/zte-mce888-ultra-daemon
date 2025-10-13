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
        """
        Initialize runtime-only attributes after dataclass construction.

        Creates an empty `calls` list used to record metrics requested from the stub.
        """
        self.calls: list[str] = []

    def fetch(self, metric: str) -> object:
        """
        Retrieve a predefined response for the given metric key.

        Parameters:
            metric (str): Metric key to look up in the reader's responses mapping.

        Returns:
            object: The value associated with `metric` in the responses mapping.

        Raises:
            KeyError: If `metric` is not present in the responses mapping.
        """
        self.calls.append(metric)
        if metric not in self.responses:
            raise KeyError(metric)
        return self.responses[metric]


@dataclass
class StubAggregator:
    def __post_init__(self) -> None:
        """
        Initialize the aggregator's call counter to zero.

        This sets an integer counter used to track how many times collection methods have been invoked.
        """
        self.calls = 0

    def collect_lte(self) -> dict[str, object]:
        """
        Provide a simulated LTE metrics snapshot.

        Also increments the internal call counter.

        Returns:
            metrics (dict[str, object]): A dictionary with LTE metric names as
                keys; currently contains "rsrp1" mapped to the signal
                strength in dBm (-92.0).
        """
        self.calls += 1
        return {"rsrp1": -92.0}


class StubMQTTClient:
    def __init__(self) -> None:
        """
        Initialize the StubMQTTClient instance.

        Creates an empty `publishes` list used to record published MQTT envelopes for inspection in tests.
        """
        self.publishes: list[object] = []

    def publish(self, envelope: object) -> None:
        """
        Record an MQTT envelope for later inspection by test code.

        Parameters:
            envelope (object): The MQTT envelope to publish; stored in the
                client's internal list for assertions.
        """
        self.publishes.append(envelope)


@pytest.fixture()
def dispatcher_setup() -> tuple[Dispatcher, StubMetricReader, StubAggregator, StubMQTTClient]:
    """
    Create a Dispatcher configured for tests and its stubbed dependencies.

    Returns:
        tuple: A 4-tuple containing:
            - Dispatcher: the Dispatcher instance configured with a local MQTTConfig and the provided stubs.
            - StubMetricReader: a stub metric reader preloaded with {"provider": "O2"}.
            - StubAggregator: a stub aggregator instance.
            - StubMQTTClient: a stub MQTT client that records published envelopes.
    """
    metric_reader = StubMetricReader({"provider": "O2"})
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


def test_single_metric_request_triggers_publish(
    dispatcher_setup: tuple[Dispatcher, StubMetricReader, StubAggregator, StubMQTTClient],
) -> None:
    dispatcher, metric_reader, aggregator, mqtt_client = dispatcher_setup

    dispatcher.handle_request("ZTE/Provider/GET")

    assert metric_reader.calls == ["provider"]
    assert aggregator.calls == 0
    assert mqtt_client.publishes, "publish should have been invoked"

    envelope = mqtt_client.publishes[0]
    assert envelope.topic == "zte/provider"
    assert envelope.payload == "O2"
    assert envelope.qos == 0
    assert envelope.retain is False
