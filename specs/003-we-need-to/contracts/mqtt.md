# MQTT Contract — ZTE Daemon (`zte run`)

## Topics
- Root topic: `<root>` (default: `zte`)
- Request (single metric): `<root>/<metric>/get`
- Request (aggregate LTE): `<root>/lte/get`
- Response (single metric): `<root>/<metric>`
- Response (aggregate LTE): `<root>/lte`

Normalization: Entire topic path is lowercased.

## Payloads
- Single metric response: JSON scalar value only (e.g., `"O2"`, `-92.0`).
- Aggregate LTE response: JSON object mapping metric identifiers to values per `/docs/metrics.md` (e.g., `{ "lte": { "rsrp1": -92.0, ... } }` or a flat object for LTE keys—see examples below).

Examples:
- Request: `mosquitto_pub -h 192.168.0.242 -t 'zte/provider/get' -n`
- Response on `zte/provider`: `"O2"`
- Request: `mosquitto_pub -h 192.168.0.242 -t 'zte/lte/get' -n`
- Response on `zte/lte` (object excerpt):
  ```json
  {
    "rsrp1": -92.0,
    "sinr1": 12.5,
    "rsrq": -9.0,
    "pci": 123
  }
  ```

## QoS and Retain
- QoS: 0
- Retain: false

## Authentication and Security
- Username/password supported.
- TLS: Not supported in this feature (plaintext only). A follow-up will add optional TLS flags and documentation.

## Reconnect
- Fixed retry every 5 seconds on disconnect until connected.

## Error Handling
- Unknown metric or router error: log error, do not publish a response.
- Partial aggregate failures: publish only successful keys; log failures.

## CLI Options Mapping
- `--mqtt-host`, `--mqtt-port` (default 1883), `--mqtt-username`, `--mqtt-password`, `--mqtt-topic` (root topic, default `zte`).
- Options are prefixed with `mqtt-` as required.

## Versioning
- Topic and payload schema treated as contracts; changes require migration guidance.
