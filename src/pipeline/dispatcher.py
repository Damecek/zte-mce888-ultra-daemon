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
    def collect_all(self) -> dict[str, Any]:  # pragma: no cover - protocol definition
        ...
    def collect_nr5g(self) -> dict[str, Any]:  # pragma: no cover - protocol definition
        ...
    def collect_temp(self) -> dict[str, Any]:  # pragma: no cover - protocol definition
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
            # Parse with known root and support nested metric paths like
            # zte/lte/rsrp1/get -> metric 'lte.rsrp1'
            request = MetricRequest.from_topic_for_root(topic, self._config.root_topic)
        except ValueError:
            self._logger.warning("Ignoring invalid request topic", extra={"topic": topic})
            self.state.record_failure()
            return

        # Root is validated during parsing; no separate mismatch branch needed.

        self.state.record_request(request.topic)
        response_topic = topics.build_response_topic(self._config.root_topic, request.metric)

        def _is_empty_value(value: Any) -> bool:
            if value is None:
                return True
            if isinstance(value, str):
                return value.strip() == ""
            if isinstance(value, dict):
                # Empty if all nested values are empty by this same rule
                return all(_is_empty_value(v) for v in value.values())
            if isinstance(value, (list, tuple, set)):
                return all(_is_empty_value(v) for v in value)
            return False

        try:
            if request.is_aggregate:
                if request.metric == "lte":
                    payload_obj = self.aggregator.collect_lte()
                elif request.metric == "nr5g":
                    payload_obj = self.aggregator.collect_nr5g()
                elif request.metric == "temp":
                    payload_obj = self.aggregator.collect_temp()
                else:  # "zte" top-level aggregate
                    payload_obj = self.aggregator.collect_all()
                # Guard: skip publish on effectively empty aggregates
                if not payload_obj or _is_empty_value(payload_obj):
                    self._logger.error(
                        "Aggregate request produced empty data; skipping publish",
                        extra={"topic": topic, "metric": request.metric},
                    )
                    return
            else:
                payload_obj = self.metric_reader.fetch(request.metric)
                # Guard: skip publish on empty single value
                if _is_empty_value(payload_obj):
                    self._logger.error(
                        "Metric value empty; skipping publish",
                        extra={"topic": topic, "metric": request.metric},
                    )
                    return
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
