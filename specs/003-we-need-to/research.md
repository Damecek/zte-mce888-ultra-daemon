# Phase 0 Research — MQTT-Driven ZTE Daemon (`zte run`)

## Decisions
- Topic pattern: Requests on `<root>/<metric>/get`, responses on `<root>/<metric>`; aggregate `lte/get` publishes to `<root>/lte`.
- Topic normalization: Entire topic lowercased to ensure determinism.
- Payload shape: Single metric → JSON scalar (value only). Aggregate (`lte`) → JSON object mapping metrics per `docs/metrics.md`.
- Error handling: On unknown metric or router failure, log error and publish nothing. For aggregate, publish only successful metrics; log failures.
- MQTT QoS/retain: QoS 0, retain false.
- Reconnect: Fixed retry every 5 seconds indefinitely.
- Security: Plaintext MQTT for this feature (no TLS). Local-only broker assumed; credentials supported.
- Concurrency: Sequential handling—one request at a time.
- Router params: CLI options same as `zte read` (host, password, etc.).
- Placeholders: Do not interpret placeholders like `%circuit`, `%name` in `--mqtt-topic`.

## Rationale
- Deterministic topics and lowercase normalization reduce integration friction with typical home automation setups (Home Assistant, Node-RED).
- QoS 0 + non-retained responses avoid stale reads and keep latency low for on-demand queries.
- Sequential processing simplifies correctness and state management; expected traffic volume is low.
- Plaintext MQTT aligns with clarification and local-only deployments; documenting TLS as a follow-up preserves security posture expectations in the constitution.

## Alternatives Considered
- QoS 1/2: Adds broker/device overhead without clear benefit for on-demand, idempotent fetches; declined for now.
- Retained responses: Risk of consumers reading stale values; declined for on-demand request/response.
- Concurrent request handling: Adds complexity (in-flight map, ordering); not necessary for intended scale.
- TLS in v1: Valuable, but requires broker cert provisioning, verification strategies, and CLI surface; planned as a follow-up.

## References
- Metrics catalog: /Users/adam/IdeaProjects/zte-mc888-ultra-deamon/docs/metrics.md
- Client reuse: /Users/adam/IdeaProjects/zte-mc888-ultra-deamon/src/services/zte_client.py
- CLI parity: /Users/adam/IdeaProjects/zte-mc888-ultra-deamon/src/cli/commands/read.py

## Unknowns Resolved
- Topic schema and normalization: clarified.
- Error behavior for single metric and aggregate: clarified.
- Reconnect strategy and security posture: clarified.

## Open Follow-ups
- Add optional TLS support with CLI flags and documentation.
- Add integration tests for end-to-end MQTT subscribe→dispatch→publish with a local broker.
