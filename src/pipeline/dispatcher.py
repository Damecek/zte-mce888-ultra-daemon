from __future__ import annotations

import logging
from typing import Any, Protocol

from lib import topics
from models.daemon_state import DaemonState
from models.metric_request import MetricRequest
from models.mqtt_config import MQTTConfig
from models.publish_envelope import PublishEnvelope
from services import zte_client


class MetricReader(Protocol):
    def fetch(self, metric: str) -> Any:  # pragma: no cover - protocol definition
        ...


class Aggregator(Protocol):
    def collect_lte(self) -> dict[str, Any]:  # pragma: no cover - protocol definition
        ...


class Dispatcher:
    """Coordinates MQTT request handling and publish responses."""

    def __init__(
        self,
        *,
        mqtt_config: MQTTConfig,
        metric_reader: MetricReader,
        aggregator: Aggregator,
        mqtt_client: Any,
        state: DaemonState,
        logger: logging.Logger | None = None,
    ) -> None:
        self._config = mqtt_config
        self.metric_reader = metric_reader
        self.aggregator = aggregator
        self.mqtt_client = mqtt_client
        self.state = state
        self._logger = logger or logging.getLogger("zte_daemon.dispatcher")

    def handle_request(self, topic: str, payload: bytes | None = None) -> None:
        del payload  # Requests are signaled via topic only
        try:
            request = MetricRequest.from_topic(topic)
        except ValueError:
            self._logger.warning("Ignoring invalid request topic", extra={"topic": topic})
            self.state.record_failure()
            return

        if request.root != self._config.root_topic:
            self._logger.debug(
                "Ignoring request for different root",
                extra={"topic": topic, "expected_root": self._config.root_topic},
            )
            return

        self.state.record_request(request.topic)
        response_topic = topics.build_response_topic(self._config.root_topic, request.metric)

        try:
            if request.is_aggregate:
                payload_obj = self.aggregator.collect_lte()
                if not payload_obj:
                    self._logger.warning("Aggregate request produced no data", extra={"topic": topic})
                    return
            else:
                payload_obj = self.metric_reader.fetch(request.metric)
        except KeyError:
            self._logger.warning("Requested metric unavailable", extra={"metric": request.metric})
            self.state.record_failure()
            return
        except zte_client.ZTEClientError as exc:
            self._logger.error("Router interaction failed", exc_info=exc)
            self.state.record_failure()
            return

        envelope = PublishEnvelope(topic=response_topic, payload=payload_obj)
        self.mqtt_client.publish(envelope)
        self.state.record_publish()
        self._logger.info(
            "Published metric response",
            extra={"topic": envelope.topic, "aggregate": request.is_aggregate},
        )


__all__ = ["Dispatcher"]
