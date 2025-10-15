# Phase 1 Data Model — MQTT-Driven ZTE Daemon (`zte run`)

## Entities

- MQTTConfig
  - root_topic: str (default: `zte`)
  - host: str
  - port: int (default: 1883)
  - username: str | None
  - password: str | None
  - qos: int (fixed 0)
  - retain: bool (fixed False)
  - reconnect_seconds: int (fixed 5)

- RouterConfig
  - host: str (default: `http://192.168.0.1`)
  - password: str

- MetricRequest
  - topic: str (full request topic, lowercased)
  - metric: str (e.g., `provider`, `lte`, `lte.rsrp1`)
  - is_aggregate: bool (true for `lte/get`)

- PublishEnvelope
  - topic: str (response topic)
  - payload: Any (scalar for single metric; object for aggregates)
  - qos: int (0)
  - retain: bool (False)

- DaemonState
  - connected: bool
  - last_seen_request_topic: str | None
  - last_publish_time: datetime | None
  - failures: int

## Relationships
- `MetricRequest.metric` maps to the `docs/metrics.md` identifiers and `models/metrics.py` structure for aggregates.
- `MQTTConfig.root_topic` prefixes both request (`<root>/<metric>/get`) and response (`<root>/<metric>`) topics.

## Validation Rules
- Topics are normalized to lowercase.
- Only metrics defined in `docs/metrics.md` are considered valid for single-metric requests.
- Aggregate `lte/get` composes all LTE metrics; unknown fields are omitted with errors logged.

## State Transitions
- `DaemonState.connected` toggles with broker connectivity; on disconnect, a reconnect timer (5s) is scheduled.
- Upon receiving a request, `DaemonState.last_seen_request_topic` and `last_publish_time` update after successful publish.
