from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from models.mqtt_config import MQTTConfig
from pipeline.dispatcher import Dispatcher
from services import zte_client


@dataclass
class StubState:
    requests: int = 0
    publishes: int = 0
    failures: int = 0

    def record_request(self, _: str) -> None:
        self.requests += 1

    def record_publish(self) -> None:
        self.publishes += 1

    def record_failure(self) -> None:
        self.failures += 1


class StubMQTTClient:
    def __init__(self) -> None:
        self.publishes: list[Any] = []

    def publish(self, envelope: Any) -> None:
        self.publishes.append(envelope)


class MetricReaderReturn:
    def __init__(self, value: Any) -> None:
        self.calls: list[str] = []
        self.value = value

    def fetch(self, metric: str) -> Any:
        self.calls.append(metric)
        return self.value


class MetricReaderKeyError:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def fetch(self, metric: str) -> Any:
        self.calls.append(metric)
        raise KeyError(metric)


class MetricReaderClientError:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def fetch(self, metric: str) -> Any:
        self.calls.append(metric)
        raise zte_client.ZTEClientError("router unhappy")


class AggregatorEmpty:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def collect_lte(self) -> dict[str, Any]:
        self.calls.append("lte")
        return {}

    def collect_nr5g(self) -> dict[str, Any]:
        self.calls.append("nr5g")
        return {}

    def collect_temp(self) -> dict[str, Any]:
        self.calls.append("temp")
        return {}

    def collect_all(self) -> dict[str, Any]:
        self.calls.append("zte")
        return {}


class AggregatorClientError(AggregatorEmpty):
    def collect_all(self) -> dict[str, Any]:
        self.calls.append("zte")
        raise zte_client.ZTEClientError("router unhappy")


def _make_dispatcher(
    *,
    reader: Any,
    aggregator: Any,
    mqtt_client: StubMQTTClient | None = None,
    state: StubState | None = None,
    root: str = "zte",
) -> tuple[Dispatcher, StubState, StubMQTTClient]:
    mqtt_client = mqtt_client or StubMQTTClient()
    state = state or StubState()
    config = MQTTConfig(host="mqtt.local", root_topic=root)
    dispatcher = Dispatcher(
        mqtt_config=config,
        metric_reader=reader,
        aggregator=aggregator,
        mqtt_client=mqtt_client,
        state=state,
    )
    return dispatcher, state, mqtt_client


def test_non_get_in_root_is_ignored_without_failure() -> None:
    # Topics under the root without trailing /get are response topics; ignore quietly.
    dispatcher, state, mqtt = _make_dispatcher(reader=MetricReaderReturn("x"), aggregator=AggregatorEmpty())
    dispatcher.handle_request("zte/provider")  # response topic, not a request

    assert state.failures == 0
    assert state.requests == 0  # not counted on ignored topic
    assert not mqtt.publishes


def test_aggregate_empty_skips_publish() -> None:
    # Aggregate request with empty result should not publish
    dispatcher, state, mqtt = _make_dispatcher(reader=MetricReaderReturn("x"), aggregator=AggregatorEmpty())
    dispatcher.handle_request("zte/lte/get")

    assert state.requests == 1
    assert state.publishes == 0
    assert not mqtt.publishes  # no publish on empty aggregate


def test_single_empty_skips_publish_for_whitespace() -> None:
    # Single metric request returning whitespace-only string -> treated as empty
    dispatcher, state, mqtt = _make_dispatcher(reader=MetricReaderReturn("  "), aggregator=AggregatorEmpty())
    dispatcher.handle_request("zte/provider/get")

    assert state.requests == 1
    assert state.publishes == 0
    assert not mqtt.publishes  # no publish on empty single value


def test_single_keyerror_records_failure() -> None:
    # Reader raises KeyError -> failure recorded, no publish
    dispatcher, state, mqtt = _make_dispatcher(reader=MetricReaderKeyError(), aggregator=AggregatorEmpty())
    dispatcher.handle_request("zte/provider/get")

    assert state.failures == 1
    assert state.requests == 1  # request counted before fetch
    assert not mqtt.publishes


def test_client_error_records_failure_and_no_publish() -> None:
    # Reader or aggregator raising ZTEClientError must record failure and not publish
    # Use top-level aggregate to exercise the aggregate client-error path.
    dispatcher, state, mqtt = _make_dispatcher(reader=MetricReaderReturn("x"), aggregator=AggregatorClientError())
    dispatcher.handle_request("zte/get")  # top-level aggregate ('zte')

    assert state.failures == 1
    assert state.requests == 1
    assert not mqtt.publishes
