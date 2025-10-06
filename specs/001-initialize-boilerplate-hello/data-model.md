# Data Model - Initialize Boilerplate Hello World

## CLICommand
- **Description**: Represents user-facing commands exposed via Click (`zte run`, `zte read`).
- **Fields**:
  - `name` (enum: `run`, `read`)
  - `device_host` (IPv4 string, defaults to 192.168.0.1)
  - `device_pass` (string, required for authenticated REST calls)
  - `log_level` (enum: debug, info, warn, error)
  - `foreground` (bool, default true for hello world)
  - `log_file` (filesystem path, optional)
  - `mqtt_host` (host:port string, optional placeholder)
  - `mqtt_topic` (string, default `zte-modem` placeholder)
  - `mqtt_user` / `mqtt_password` (strings, optional placeholder)
  - `metric` (string, required for `read` commands; choices include `RSRP`, `Provider`)
- **Validation**:
  - Reject public IP ranges for `device_host` without explicit override flag.
  - Normalise log levels to uppercase for logging config.

## ModemTelemetrySnapshot
- **Description**: In-memory representation of modem REST data consumed by mocks and CLI reads.
- **Fields**:
  - `timestamp` (ISO 8601 string)
  - `rsrp` (dBm integer)
  - `provider` (string)
  - `raw_payload` (dict of remaining modem fields for transparency)
- **Validation**:
  - `timestamp` must be monotonic compared to previous snapshot to maintain determinism.
  - Missing non-critical fields recorded as warnings in logs.

## MQTTPlaceholderMessage
- **Description**: Structured payload published by the hello-world daemon to illustrate future schema.
- **Fields**:
  - `schema_version` (string, e.g., `0.1.0-mock`)
  - `device_id` (string; derived from host or configured slug)
  - `metrics` (dict with `rsrp`, `provider`, `captured_at`)
  - `status` (enum: `mock`, `unreachable`, `degraded`)
- **Validation**:
  - Require `schema_version` to follow semver with `-mock` suffix for placeholder payloads.
  - Ensure metrics values mirror the `ModemTelemetrySnapshot` currently cached.

## LogEvent
- **Description**: Canonical shape for daemon logging to both stdout and file targets.
- **Fields**:
  - `timestamp` (ISO 8601 string)
  - `level` (enum: DEBUG/INFO/WARN/ERROR)
  - `component` (enum: CLI, ModemMock, MQTTMock)
  - `message` (string)
  - `context` (dict of key/value pairs; optional)
- **Validation**:
  - Enforce lower-case JSON keys for structured logging compatibility.
  - Ensure sensitive data (passwords) are never included in `context`.

## Relationships & Flow
- `CLICommand` orchestrates retrieval of `ModemTelemetrySnapshot` from the mock client.
- `ModemTelemetrySnapshot` feeds `MQTTPlaceholderMessage.metrics` when publishing.
- `LogEvent` instances document each step (mock modem fetch, MQTT publish attempt, CLI read output).
- In hello-world, no persistent storage is created; telemetry is ephemeral per invocation.
