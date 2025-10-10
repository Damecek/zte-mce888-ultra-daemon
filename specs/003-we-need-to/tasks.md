# Tasks: MQTT-Driven ZTE Daemon (`zte run`)

**Input**: Design documents from `/specs/003-we-need-to/`
**Prerequisites**: plan.md (required), research.md, data-model.md, contracts/

## Execution Flow (main)
```
1. Load plan.md from feature directory
   → If not found: ERROR "No implementation plan found"
   → Extract: tech stack, libraries, structure
2. Load optional design documents:
   → data-model.md: Extract entities
   → contracts/: Each file → MQTT contract test task
   → research.md: Extract decisions → setup and constraints
   → quickstart.md: Extract user scenarios → integration tests
3. Generate tasks by category:
   → Setup: CLI wiring, dependencies, linting
   → Tests: contract tests and integration scenarios
   → Core: models, dispatcher, MQTT client, CLI command
   → Integration: sequencing, reconnects, logging
   → Polish: unit tests, performance, docs
4. Apply task rules:
   → Different files = mark [P] for parallel
   → Same file = sequential (no [P])
   → Prefer tests early (TDD)
5. Number tasks sequentially (T001, T002...)
6. Note dependencies and parallel groups
7. Create parallel execution examples with actual commands
```

## Format: `[ID] [P?] Description`
- [P]: Can run in parallel (different files, no dependencies)
- Include exact file paths in descriptions

## Phase 3.1: Setup
- [ ] T001 Ensure CLI entry exists and visible: validate `src/cli/commands/run.py` is registered under `src/cli/zte.py`; add TODO comments for real gmqtt wiring. Files: `src/cli/commands/run.py`, `src/cli/zte.py`
- [ ] T002 Add topic parsing utilities skeleton for normalization and matching. File: `src/lib/topics.py` (new)
- [ ] T003 [P] Verify dev tooling baselines run clean. Commands: `uv run pytest -q` (may fail due to missing tests), `ruff check .`. No code files modified.

## Phase 3.2: Tests & Coverage
Goal: Add tests first to drive implementation per contracts and scenarios.
- [ ] T004 [P] Contract test for MQTT topics/payloads per `specs/003-we-need-to/contracts/mqtt.md`. File: `tests/contract/test_mqtt_contract.py`. Covers: lowercase topics, QoS=0, retain=False, single metric scalar payload, LTE aggregate object payload.
- [ ] T005 [P] Integration test: Single metric request→publish (quickstart "provider"). File: `tests/integration/test_single_metric_request.py`. Arrange: start daemon in test mode, simulate `'<root>/provider/get'` message, assert publish on `'<root>/provider'` with JSON scalar.
- [ ] T006 [P] Integration test: LTE aggregate request→publish. File: `tests/integration/test_aggregate_lte_request.py`. Arrange: simulate `'<root>/lte/get'`, assert object payload keys per `docs/metrics.md`/`src/models/metrics.py`.

## Phase 3.3: Core Implementation (ONLY after tests are failing)
- [ ] T007 Define `MQTTConfig` dataclass. File: `src/models/mqtt_config.py` (new). Fields: root_topic, host, port=1883, username, password, qos=0 (fixed), retain=False (fixed), reconnect_seconds=5 (fixed).
- [ ] T008 [P] Define `RouterConfig` dataclass. File: `src/models/router_config.py` (new). Fields: host (default `http://192.168.0.1`), password.
- [ ] T009 [P] Define `MetricRequest` dataclass. File: `src/models/metric_request.py` (new). Fields: topic (lowercased), metric, is_aggregate.
- [ ] T010 [P] Define `PublishEnvelope` dataclass. File: `src/models/publish_envelope.py` (new). Fields: topic, payload (Any), qos=0, retain=False.
- [ ] T011 [P] Define `DaemonState` dataclass. File: `src/models/daemon_state.py` (new). Fields: connected: bool, last_seen_request_topic: str|None, last_publish_time: datetime|None, failures: int.
- [ ] T012 Implement topic normalization and parse helpers. File: `src/lib/topics.py`. Functions: `normalize(topic: str)->str`, `parse_request(root: str, topic: str)->MetricRequest|None` mapping `<root>/<metric>/get` and aggregate `lte/get`.
- [ ] T013 Build dispatcher to handle requests sequentially. File: `src/pipeline/dispatcher.py` (new). Responsibilities: subscribe callbacks accept normalized topic, call `services/zte_client.py` to fetch metric(s) or aggregate via `src/models/metrics.py`, publish via MQTT client wrapper.
- [ ] T014 Implement gmqtt client wrapper. File: `src/services/mqtt_client.py` (new). Responsibilities: connect, authenticate, subscribe to `f"{root}/+/get"` and `f"{root}/lte/get"`, publish with QoS=0 retain=False, auto-reconnect every 5s.
- [ ] T015 Wire CLI `zte run` to real daemon. File: `src/cli/commands/run.py`. Replace mock path: instantiate configs, gmqtt client, dispatcher; foreground mode runs loop; keep `--rest-test` behavior for minimal modem probe using `services/zte_client.py`.
- [ ] T016 Implement LTE aggregate builder. File: `src/services/metrics_aggregator.py` (new). Use `src/services/zte_client.py` and `src/models/metrics.py` to compose LTE object payload.

## Phase 3.4: Integration
- [ ] T017 Add sequential handling guard. File: `src/pipeline/dispatcher.py`. Implement an async lock to ensure one in-flight request at a time.
- [ ] T018 Reconnect strategy. File: `src/services/mqtt_client.py`. On disconnect, schedule reconnect every 5s until success.
- [ ] T019 Enforce contract defaults in publishing. File: `src/services/mqtt_client.py`. Ensure QoS=0 and retain=False are fixed.
- [ ] T020 Structured logging. Files: `src/cli/commands/run.py`, `src/services/mqtt_client.py`, `src/pipeline/dispatcher.py`. Log config, connectivity, and runtime events distinctly using `lib/logging_setup.py`.

## Phase 3.5: Polish
- [ ] T021 [P] Unit tests for model dataclasses. Files: `tests/unit/test_models_config.py`, `tests/unit/test_models_requests.py`, `tests/unit/test_models_state.py`.
- [ ] T022 [P] Performance/latency budget smoke test for request→publish path. File: `tests/perf/test_latency_budget.py`.
- [ ] T023 [P] Documentation updates for operator usage. Files: `docs/mqtt.md`, `docs/cli.md`, `docs/operations.md` (new). Sync examples with `specs/003-we-need-to/contracts/mqtt.md` and `quickstart.md`.
- [ ] T024 Update feature docs if schemas evolved. Files: `specs/003-we-need-to/contracts/mqtt.md`, `specs/003-we-need-to/quickstart.md`.

## Dependencies
- Setup (T001–T003) precedes all.
- Tests (T004–T006) precede Core implementation (T007–T016).
- Models (T007–T011) precede dispatcher and client (T013–T015).
- Dispatcher (T013) precedes CLI wiring (T015).
- Aggregator (T016) required for LTE route before integration tests pass.
- Integration tasks (T017–T020) after core wiring.
- Polish (T021–T024) last.

## Parallel Example
```
# Group contract and integration tests (parallel ready):
uv run pytest -q tests/contract/test_mqtt_contract.py
uv run pytest -q tests/integration/test_single_metric_request.py
uv run pytest -q tests/integration/test_aggregate_lte_request.py

# After models are stubbed (different files → [P]):
# Implement dataclasses in parallel across separate files
Task: "Define MQTTConfig in src/models/mqtt_config.py"
Task: "Define RouterConfig in src/models/router_config.py"
Task: "Define MetricRequest in src/models/metric_request.py"
Task: "Define PublishEnvelope in src/models/publish_envelope.py"
Task: "Define DaemonState in src/models/daemon_state.py"

# Quick developer checks during iteration:
ruff check .
uv run pytest -q
```

## Notes
- [P] tasks = different files, no dependencies; avoid concurrent edits to the same file.
- Tests should fail before implementation; keep TDD loop tight.
- Use `src/services/zte_client.py` and `src/models/metrics.py` for data access and shaping.
- Enforce lowercase topics, QoS=0, retain=False consistently through `src/services/mqtt_client.py`.
- Prefer foreground mode during tests; no real MQTT broker required—use gmqtt client with an in-process event loop and test doubles.

