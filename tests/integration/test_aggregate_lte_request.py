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
        Initialize runtime state for the dataclass by creating an empty list used to record metric fetch calls.
        """
        self.calls: list[str] = []

    def fetch(self, metric: str) -> object:
        """
        Record a metric fetch call and return the configured response for that metric.

        Parameters:
            metric (str): Name of the metric to fetch.

        Returns:
            object: The value configured for `metric` in `responses`.

        Raises:
            KeyError: If no response is configured for `metric`.
        """
        self.calls.append(metric)
        if metric not in self.responses:
            raise KeyError(metric)
        return self.responses[metric]


@dataclass
class StubAggregator:
    payload: dict[str, object]

    def __post_init__(self) -> None:
        """
        Initialize the instance's call counter.

        Sets the attribute `calls` to 0 to track the number of times collection methods are invoked.
        """
        self.calls = 0

    def collect_lte(self) -> dict[str, object]:
        """
        Record that an LTE aggregation was requested and return the predefined aggregation payload.

        Returns:
            dict[str, object]: The predefined payload mapping metric names to their values.
        """
        self.calls += 1
        return self.payload


class StubMQTTClient:
    def __init__(self) -> None:
        """
        Initialize the test MQTT client that records published envelopes.

        Creates an empty `publishes` list which will hold envelope objects passed to `publish`.
        """
        self.publishes: list[object] = []

    def publish(self, envelope: object) -> None:
        """
        Record an MQTT envelope in the client's published messages list.

        Parameters:
            envelope (object): The MQTT message envelope that was published;
                appended to the client's internal `publishes` list.
        """
        self.publishes.append(envelope)


@pytest.fixture()
def dispatcher_setup() -> tuple[Dispatcher, StubMetricReader, StubAggregator, StubMQTTClient]:
    """
    Create a Dispatcher wired with lightweight test doubles for integration
    testing.

    Sets up a StubMetricReader preloaded with {"provider": "O2"}, a
    StubAggregator that returns a fixed LTE aggregation payload, a
    StubMQTTClient that records published envelopes, a DaemonState, and an
    MQTTConfig targeting "mqtt.local", then constructs and returns a
    Dispatcher using those objects.

    Returns:
        (dispatcher, metric_reader, aggregator, mqtt_client):
            dispatcher — Dispatcher configured with the test doubles and state.
            metric_reader — StubMetricReader initialized with a single
            "provider" response.
            aggregator — StubAggregator that returns the predefined LTE payload.
            mqtt_client — StubMQTTClient that records published envelopes.
    """
    metric_reader = StubMetricReader({"provider": "O2"})
    aggregate_payload = {"rsrp1": -92.0, "sinr1": 12.5, "rsrq": -9.0, "pci": 123}
    aggregator = StubAggregator(aggregate_payload)
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


def test_aggregate_request_uses_aggregator(
    dispatcher_setup: tuple[Dispatcher, StubMetricReader, StubAggregator, StubMQTTClient],
) -> None:
    dispatcher, metric_reader, aggregator, mqtt_client = dispatcher_setup

    dispatcher.handle_request("zte/lte/get")

    assert metric_reader.calls == []
    assert aggregator.calls == 1
    assert mqtt_client.publishes, "aggregate publish expected"

    envelope = mqtt_client.publishes[0]
    assert envelope.topic == "zte/lte"
    assert envelope.payload == aggregator.payload
    assert isinstance(envelope.payload, dict)
    assert envelope.qos == 0
    assert envelope.retain is False
