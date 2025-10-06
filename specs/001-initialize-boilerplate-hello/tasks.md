# Tasks: Initialize Boilerplate Hello World

## Phase: Setup
- [X] T001 Create Python project scaffolding with uv-compatible `pyproject.toml`, package directories under `src/zte_daemon/`, and empty `tests/__init__.py` so pytest discovers suites.
- [X] T002 Establish test fixture layout by adding modem sample JSON under `tests/fixtures/modem/` and helper factory module `tests/fixtures/__init__.py` for loading snapshots.

## Phase: Tests (write before implementations)
- [X] T003 [P] Add CLI help contract tests in `tests/unit/test_cli_help.py` covering `zte`, `zte run --help`, and `zte read --help` output snippets.
- [X] T004 Write failing unit tests in `tests/unit/test_cli_run.py` asserting `zte run` loads modem fixtures, configures logging, records MQTT publish attempt, and emits friendly greeting text.
- [X] T005 [P] Write unit tests in `tests/unit/test_cli_read.py` ensuring `zte read <metric>` prints requested telemetry and errors on unknown metrics.
- [X] T006 [P] Write modem mock tests in `tests/unit/test_modem_mock.py` validating fixture parsing, timestamp monotonicity, and helpful error messaging when fixtures missing.
- [X] T007 [P] Write MQTT placeholder tests in `tests/unit/test_mqtt_mock.py` asserting payload schema fields and publish recording semantics.
- [X] T008 Create integration test `tests/integration/test_hello_world_flow.py` exercising CLI group end-to-end with both commands.

## Phase: Core Implementation
- [X] T009 Implement structured logging utilities in `src/zte_daemon/logging/config.py` returning configured logger and JSON formatter per spec defaults.
- [X] T010 Implement modem mock client in `src/zte_daemon/modem/mock_client.py` to load fixtures, cache snapshots, and surface metrics for CLI/testing.
- [X] T011 Implement MQTT mock broker in `src/zte_daemon/mqtt/mock_broker.py` that records messages and warns when broker details missing.
- [X] T012 Implement CLI `run` command in `src/zte_daemon/cli/commands/run.py` orchestrating modem snapshot fetch, MQTT publish via mock, and structured logging/console output.
- [X] T013 Implement CLI `read` command in `src/zte_daemon/cli/commands/read.py` retrieving cached telemetry metrics with validation and logging.
- [X] T014 Implement CLI entry group in `src/zte_daemon/cli/main.py` wiring Click command group, options, and console script hook.

## Phase: Integration
- [X] T015 Register console script entry point `zte` in `pyproject.toml` and ensure package exposes `zte_daemon.cli.main:cli` for uv usage.
- [X] T016 Provide project-level README with instructions drawn from quickstart and fixture workflow (`README.md`).

## Phase: Polish
- [X] T017 [P] Add documentation tests in `tests/unit/test_docs_links.py` verifying README quickstart commands mention `uv run pytest` and fixture guidance.
- [X] T018 [P] Run pytest to confirm suite passes and update tasks as complete.
