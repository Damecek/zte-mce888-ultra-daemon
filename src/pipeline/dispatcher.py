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
        """
        Retrieve the current value for the specified metric.
        
        Parameters:
            metric (str): The name of the metric to retrieve.
        
        Returns:
            Any: The metric's value; the concrete type depends on the metric (e.g., number, string, mapping).
        """
        ...


class Aggregator(Protocol):
    def collect_lte(self) -> dict[str, Any]:  # pragma: no cover - protocol definition
        """
        Collect aggregated LTE metrics for publishing.
        
        Returns:
            dict[str, Any]: A mapping of metric names to their aggregated values (may be empty).
        """
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
        """
        Initialize the Dispatcher with its required dependencies and an optional logger.
        
        Parameters:
            mqtt_config (MQTTConfig): Configuration for MQTT topics and behavior.
            metric_reader (MetricReader): Source for fetching individual metric values.
            aggregator (Aggregator): Source for collecting aggregated metric data.
            mqtt_client (Any): MQTT client used to publish responses.
            state (DaemonState): Object used to record request and publish state.
            logger (logging.Logger | None): Optional logger; a default logger named
                "zte_daemon.dispatcher" is used if not provided.
        """
        self._config = mqtt_config
        self.metric_reader = metric_reader
        self.aggregator = aggregator
        self.mqtt_client = mqtt_client
        self.state = state
        self._logger = logger or logging.getLogger("zte_daemon.dispatcher")

    def handle_request(self, topic: str, payload: bytes | None = None) -> None:
        """
        Handle an incoming MQTT metric request identified by its topic.
        
        Parses the topic into a MetricRequest, validates it against the configured root topic, obtains the requested metric payload (single metric or aggregate), and publishes the response to the corresponding response topic. Records request, publish, and failure events in the daemon state and logs notable conditions (invalid topic, root mismatch, missing data, router errors).
        
        Parameters:
        	topic (str): MQTT topic that encodes the metric request.
        	payload (bytes | None): Ignored; requests are signaled via the topic only.
        """
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