# Tasks: MQTT-Driven ZTE Daemon (zte run)

**Input**: Design documents from `/Users/adam/IdeaProjects/zte-mc888-ultra-deamon/specs/003-we-need-to/`
**Prerequisites**: plan.md (required), research.md, data-model.md, contracts/

## Execution Flow (main)
```
1. Load plan.md from feature directory
   → If not found: ERROR "No implementation plan found"
   → Extract: tech stack, libraries, structure
2. Load optional design documents:
   → data-model.md: Extract entities → model tasks
   → contracts/: Each file → MQTT contract test task
   → research.md: Extract decisions → setup tasks
   → quickstart.md: Extract scenarios → integration tests
3. Generate tasks by category:
   → Setup: environment, deps, linting
   → Tests (TDD): contract, integration, unit
   → Core: models, services, pipeline, CLI
   → Integration: wiring, logging, constraints
   → Polish: unit tests, performance, docs
4. Apply task rules:
   → Different files = mark [P] for parallel
   → Same file = sequential (no [P])
   → Prefer tests early; ensure coverage
5. Number tasks sequentially (T001, T002...)
6. Add dependency notes and parallel examples
7. Validate task completeness and return SUCCESS
```

## Format: `[ID] [P?] Description`
- [P]: Can run in parallel (different files, no dependencies)
- Include exact file paths in descriptions

## Phase 3.1: Setup
- [ ] T001 Validate Python runtime and tooling: ensure `uv`, Python 3.12 (uv-managed), `pytest`, `ruff`, and `gmqtt` are configured. Verify CLI entry works: `uv run zte --help`.
- [ ] T002 [P] Add/verify `gmqtt` dependency in `pyproject.toml` and lock via `uv pip compile` if needed; run `uv run pytest -q` smoke to confirm environment.

## Phase 3.2: Tests (TDD)
Goal: Write failing tests first based on contracts and scenarios.
- [ ] T003 [P] Contract test for MQTT topics and payloads per `specs/003-we-need-to/contracts/mqtt.md` in `tests/contract/test_mqtt_contract.py` (topics lowercase, request/response mapping, QoS 0, retain false, scalar vs object payloads).
- [ ] T004 [P] Integration test: single metric request→publish flow using mocks in `tests/integration/test_single_metric_request.py` (simulate subscribe on `<root>/provider/get`, expect publish to `<root>/provider` with scalar payload).
- [ ] T005 [P] Integration test: aggregate LTE request→publish flow in `tests/integration/test_aggregate_lte_request.py` (simulate `<root>/lte/get`, expect object payload to `<root>/lte` per `docs/metrics.md`).
- [ ] T006 [P] Unit tests for models in `tests/unit/`:
  - `tests/unit/test_models_config.py` (MQTTConfig, RouterConfig defaults/validation)
  - `tests/unit/test_models_requests.py` (MetricRequest parsing, is_aggregate)
  - `tests/unit/test_models_state.py` (DaemonState transitions)

## Phase 3.3: Core Implementation (ONLY after tests are failing)
- [ ] T007 [P] Implement model `MQTTConfig` in `src/models/mqtt_config.py` (root topic default `zte`, host, port 1883, username/password optional, qos=0, retain=False, reconnect_seconds=5).
- [ ] T008 [P] Implement model `RouterConfig` in `src/models/router_config.py` (host default `http://192.168.0.1`, password required; parity with `src/cli/commands/read.py` options).
- [ ] T009 [P] Implement model `MetricRequest` in `src/models/metric_request.py` (fields: topic, metric, is_aggregate; ensure lowercase normalization and detection of `lte/get`).
- [ ] T010 [P] Implement model `PublishEnvelope` in `src/models/publish_envelope.py` (topic, payload, qos=0, retain=False).
- [ ] T011 [P] Implement model `DaemonState` in `src/models/daemon_state.py` (connected flag, last_seen_request_topic, last_publish_time, failures).
- [ ] T012 [P] Implement topic utilities in `src/lib/topics.py` (normalize to lowercase; build request/response topics; parse `<root>/<metric>/get`).
- [ ] T013 Implement LTE metrics aggregator in `src/services/metrics_aggregator.py` (compose LTE object from `services/zte_client.py` lookups; omit unknowns; log failures).
- [ ] T014 Implement gmqtt wrapper client in `src/services/mqtt_client.py` (connect, subscribe to `<root>/+/get` and `<root>/lte/get`, publish with QoS 0 retain False, reconnect every 5s).
- [ ] T015 Implement dispatcher in `src/pipeline/dispatcher.py` to handle incoming topics, create `MetricRequest`, fetch via `services/zte_client.py` or `services/metrics_aggregator.py`, and publish via `mqtt_client`.
- [ ] T016 Wire CLI command in `src/cli/commands/run.py` to configure models, initialize `mqtt_client`, `dispatcher`, and run foreground mode; add flags for router and MQTT (mirroring `read`).

## Phase 3.4: Integration
- [ ] T017 Add structured logging within `src/lib/logging_setup.py` usage across `mqtt_client`, `dispatcher`, and CLI; ensure clear connect/disconnect/request/publish logs.
- [ ] T018 Enforce local-network and plaintext constraints in code paths (documented in logs); explicitly set QoS=0 and retain=False on publish; ensure topics are lowercased.

## Phase 3.5: Polish
- [ ] T019 [P] Unit tests for `src/services/metrics_aggregator.py` and `src/lib/topics.py` in `tests/unit/` (edge cases, invalid metrics, topic normalization).
- [ ] T020 [P] Documentation updates: add CLI `zte run` section and MQTT topic examples to `docs/` (e.g., `docs/mqtt.md`, `docs/cli.md`), referencing `specs/003-we-need-to/contracts/mqtt.md` and Quickstart.
- [ ] T021 [P] Lint and format: `uv run ruff check .` and address findings; ensure CI passes.
- [ ] T022 Performance sanity: manual latency capture using local broker; store example payloads under `tests/fixtures/mqtt/` (optional).

## Dependencies
- Setup (T001–T002) precedes all tests and implementation.
- Tests (T003–T006) precede Core Implementation (T007–T016).
- Models (T007–T011) precede Services/Pipeline (T013–T016).
- Topic utils (T012) precede Dispatcher (T015) and tests that parse topics.
- Aggregator (T013) precedes Dispatcher (T015) handling of `lte/get`.
- CLI wiring (T016) follows Services and Dispatcher.
- Integration (T017–T018) follows Core Implementation.
- Polish (T019–T022) follows Integration.

## Parallel Example
```
# Contract + integration tests can run together:
uv run pytest tests/contract/test_mqtt_contract.py -q
uv run pytest tests/integration/test_single_metric_request.py -q
uv run pytest tests/integration/test_aggregate_lte_request.py -q

# Model implementations can proceed in parallel (different files):
$EDITOR src/models/mqtt_config.py &
$EDITOR src/models/router_config.py &
$EDITOR src/models/metric_request.py &
$EDITOR src/models/publish_envelope.py &
$EDITOR src/models/daemon_state.py &

# After models: implement services in sequence due to dependencies
$EDITOR src/services/metrics_aggregator.py
$EDITOR src/services/mqtt_client.py
$EDITOR src/pipeline/dispatcher.py

# Verify lint
uv run ruff check .
```

## Notes
- [P] tasks = different files, no dependencies; keep sequential where files overlap.
- Write tests to fail first; implement to pass; keep coverage on critical paths.
- Log connectivity, request handling, and publish outcomes for observability.
- Use `uv run zte run --help` to validate CLI flags and docs.

## Validation Checklist
- [ ] Contract file `contracts/mqtt.md` has corresponding test task and assertions.
- [ ] Quickstart scenarios covered by integration tests.
- [ ] Entities from `data-model.md` implemented as models with unit tests.
- [ ] Dispatcher and aggregator cover single and aggregate flows.
- [ ] Topics are lowercased; QoS=0; retain=False; reconnect=5s.
- [ ] Documentation updated; lint passes; CI green.

