# Tasks: Initialize Boilerplate Hello World

**Input**: Design documents from `/Users/adam/IdeaProjects/zte-mc888-ultra-deamon/specs/001-initialize-boilerplate-hello/`
**Prerequisites**: plan.md (required), research.md, data-model.md, contracts/

## Execution Flow (main)
1. Setup environment and skeleton per plan
2. Write failing tests from contracts and user stories
3. Implement core entities, CLI commands, and mocks
4. Wire logging and validations
5. Finalize docs and polish

## Format: `[ID] [P] Description`
- [P] indicates task can run in parallel (different files, no dependencies)
- All file paths are absolute

## Phase 3.1: Setup
- [ ] T001 Create repository structure and `pyproject.toml`
  - Files: 
    - `/Users/adam/IdeaProjects/zte-mc888-ultra-deamon/src/zte_daemon/__init__.py`
    - `/Users/adam/IdeaProjects/zte-mc888-ultra-deamon/src/zte_daemon/cli/__init__.py`
    - `/Users/adam/IdeaProjects/zte-mc888-ultra-deamon/src/zte_daemon/cli/main.py`
    - `/Users/adam/IdeaProjects/zte-mc888-ultra-deamon/src/zte_daemon/cli/commands/run.py`
    - `/Users/adam/IdeaProjects/zte-mc888-ultra-deamon/src/zte_daemon/cli/commands/read.py`
    - `/Users/adam/IdeaProjects/zte-mc888-ultra-deamon/src/zte_daemon/modem/__init__.py`
    - `/Users/adam/IdeaProjects/zte-mc888-ultra-deamon/src/zte_daemon/modem/mock_client.py`
    - `/Users/adam/IdeaProjects/zte-mc888-ultra-deamon/src/zte_daemon/mqtt/__init__.py`
    - `/Users/adam/IdeaProjects/zte-mc888-ultra-deamon/src/zte_daemon/mqtt/mock_broker.py`
    - `/Users/adam/IdeaProjects/zte-mc888-ultra-deamon/src/zte_daemon/logging/__init__.py`
    - `/Users/adam/IdeaProjects/zte-mc888-ultra-deamon/src/zte_daemon/logging/config.py`
    - `/Users/adam/IdeaProjects/zte-mc888-ultra-deamon/tests/__init__.py`
  - Command: Define uv/Click entrypoint in `pyproject.toml` with `[project.scripts] zte = "zte_daemon.cli.main:cli"`

- [ ] T002 Initialize uv and dependencies per quickstart
  - Command: `uv init . --package && uv python install 3.12 && uv add click gmqtt pytest pytest-asyncio anyio rich`
  - Note: If offline, stage dependency additions but do not install.

- [ ] T003 [P] Configure linting/formatting and CI hooks
  - Files:
    - `/Users/adam/IdeaProjects/zte-mc888-ultra-deamon/ruff.toml`
    - `/Users/adam/IdeaProjects/zte-mc888-ultra-deamon/.editorconfig`
  - Command: `uv add ruff` and add `ruff check .` to CI instructions.

## Phase 3.2: Tests First (TDD) — MUST FAIL BEFORE 3.3
- [ ] T004 [P] Contract test: CLI help matches spec
  - File: `/Users/adam/IdeaProjects/zte-mc888-ultra-deamon/tests/contract/test_cli_help.py`
  - Source: `/Users/adam/IdeaProjects/zte-mc888-ultra-deamon/specs/001-initialize-boilerplate-hello/contracts/cli-help.md`
  - Command: Implement assertions for `zte --help`, `zte run --help`, `zte read --help`.

- [ ] T005 [P] Contract test: Modem mock fixture shape
  - File: `/Users/adam/IdeaProjects/zte-mc888-ultra-deamon/tests/contract/test_modem_fixture_schema.py`
  - Source: `/Users/adam/IdeaProjects/zte-mc888-ultra-deamon/specs/001-initialize-boilerplate-hello/contracts/modem/mock-status.json`
  - Command: Validate keys `timestamp`, `signal.rsrp`, `provider`, `network.connection_state` exist and types.

- [ ] T006 [P] Contract test: MQTT hello-world payload schema
  - File: `/Users/adam/IdeaProjects/zte-mc888-ultra-deamon/tests/contract/test_mqtt_placeholder_payload.py`
  - Source: `/Users/adam/IdeaProjects/zte-mc888-ultra-deamon/specs/001-initialize-boilerplate-hello/contracts/mqtt/hello-world-message.json`
  - Command: Assert `schema_version` endswith `-mock`, metrics map has `rsrp`, `provider`, `captured_at`.

- [ ] T007 [P] Integration test: hello-world run flow (mocked)
  - File: `/Users/adam/IdeaProjects/zte-mc888-ultra-deamon/tests/integration/test_hello_world_flow.py`
  - Command: Run `zte run` with defaults; expect structured logs, mock MQTT record written, exit code 0.

- [ ] T008 [P] Integration test: interactive reads
  - File: `/Users/adam/IdeaProjects/zte-mc888-ultra-deamon/tests/integration/test_cli_read.py`
  - Command: `zte read RSRP` and `zte read Provider` return values from snapshot.

- [ ] T009 Unit test: logging config
  - File: `/Users/adam/IdeaProjects/zte-mc888-ultra-deamon/tests/unit/test_logging_config.py`
  - Command: Assert level normalization, file handler creation, and PII redaction.

## Phase 3.3: Core Implementation (ONLY after tests are failing)
- [ ] T010 [P] Implement entity: `CLICommand`
  - File: `/Users/adam/IdeaProjects/zte-mc888-ultra-deamon/src/zte_daemon/cli/commands/__init__.py`
  - Command: Define enums/validation helpers for command names, log level normalization, and local-only host checks.

- [ ] T011 [P] Implement entity: `ModemTelemetrySnapshot`
  - File: `/Users/adam/IdeaProjects/zte-mc888-ultra-deamon/src/zte_daemon/modem/mock_client.py`
  - Command: Provide dataclass and loader from fixture path `/Users/adam/IdeaProjects/zte-mc888-ultra-deamon/tests/fixtures/modem/latest.json` with monotonic timestamp checks.

- [ ] T012 [P] Implement entity: `MQTTPlaceholderMessage`
  - File: `/Users/adam/IdeaProjects/zte-mc888-ultra-deamon/src/zte_daemon/mqtt/mock_broker.py`
  - Command: Construct payload with `schema_version=0.1.0-mock`, device_id, metrics, status `mock`.

- [ ] T013 [P] Implement entity: `LogEvent` and logging config
  - File: `/Users/adam/IdeaProjects/zte-mc888-ultra-deamon/src/zte_daemon/logging/config.py`
  - Command: Structured JSON logging, stdout + optional file, redact secrets, lower-case keys.

- [ ] T014 Implement CLI group `zte` with `run` and `read`
  - File: `/Users/adam/IdeaProjects/zte-mc888-ultra-deamon/src/zte_daemon/cli/main.py`
  - Command: Use Click to register `run` and `read`; wire options from contracts.

- [ ] T015 Implement `run` command behavior (mocked modem + MQTT)
  - File: `/Users/adam/IdeaProjects/zte-mc888-ultra-deamon/src/zte_daemon/cli/commands/run.py`
  - Command: Load snapshot from fixture, log greetings, build MQTTPlaceholderMessage, append to `/Users/adam/IdeaProjects/zte-mc888-ultra-deamon/logs/mqtt-mock.jsonl`.

- [ ] T016 Implement `read` command behavior
  - File: `/Users/adam/IdeaProjects/zte-mc888-ultra-deamon/src/zte_daemon/cli/commands/read.py`
  - Command: Print metric from current snapshot; validate metric choices.

## Phase 3.4: Integration
- [ ] T017 Enforce local-network constraints for `--device-host`
  - File: `/Users/adam/IdeaProjects/zte-mc888-ultra-deamon/src/zte_daemon/cli/commands/run.py`
  - Command: Reject public IPs unless explicit override flag is set (documented warning).

- [ ] T018 Record mock MQTT publishes deterministically
  - File: `/Users/adam/IdeaProjects/zte-mc888-ultra-deamon/src/zte_daemon/mqtt/mock_broker.py`
  - Command: Append JSONL with timestamp, topic, payload; no socket connections.

## Phase 3.5: Polish
- [ ] T019 [P] Unit tests for CLI argument validation
  - File: `/Users/adam/IdeaProjects/zte-mc888-ultra-deamon/tests/unit/test_cli_args.py`
  - Command: Validate log level normalization, host validation, required flags.

- [ ] T020 [P] Documentation updates and samples
  - Files: 
    - `/Users/adam/IdeaProjects/zte-mc888-ultra-deamon/specs/001-initialize-boilerplate-hello/quickstart.md`
    - `/Users/adam/IdeaProjects/zte-mc888-ultra-deamon/specs/001-initialize-boilerplate-hello/contracts/mqtt/hello-world-message.json`
  - Command: Ensure examples match implemented CLI help and payloads; add capture instructions.

- [ ] T021 Prepare minimal CI job docs for lint + tests
  - File: `/Users/adam/IdeaProjects/zte-mc888-ultra-deamon/CONTRIBUTING.md`
  - Command: Document `uv run pytest` and `ruff check .` flows.

## Dependencies
- T001 → T002, T003, T004–T009 (tests need paths)
- T004–T009 (tests) → T010–T016 (implementation)
- T010–T016 → T017–T018 (integration)
- T014 depends on T010–T013 for shared validators and logging
- T019–T021 depend on core implementation and passing tests

## Parallel Execution Examples
```
# Contract tests in parallel (independent files):
Task: "T004 Contract test CLI help" → /Users/adam/IdeaProjects/zte-mc888-ultra-deamon/tests/contract/test_cli_help.py
Task: "T005 Contract test modem fixture" → /Users/adam/IdeaProjects/zte-mc888-ultra-deamon/tests/contract/test_modem_fixture_schema.py
Task: "T006 Contract test MQTT payload" → /Users/adam/IdeaProjects/zte-mc888-ultra-deamon/tests/contract/test_mqtt_placeholder_payload.py

# Entity implementations in parallel after tests fail:
Task: "T011 ModemTelemetrySnapshot" → /Users/adam/IdeaProjects/zte-mc888-ultra-deamon/src/zte_daemon/modem/mock_client.py
Task: "T012 MQTTPlaceholderMessage" → /Users/adam/IdeaProjects/zte-mc888-ultra-deamon/src/zte_daemon/mqtt/mock_broker.py
Task: "T013 Logging config" → /Users/adam/IdeaProjects/zte-mc888-ultra-deamon/src/zte_daemon/logging/config.py
```

## Task Agent Commands (examples)
- Initialize deps: `uv init . --package && uv python install 3.12 && uv add click gmqtt pytest pytest-asyncio anyio rich ruff`
- Run tests: `uv run pytest`
- Lint: `uv run ruff check .`

## Validation Checklist
- [ ] All contract files mapped to test tasks: CLI help, modem fixture, MQTT payload
- [ ] Entities from data model have implementation tasks: CLICommand, ModemTelemetrySnapshot, MQTTPlaceholderMessage, LogEvent
- [ ] Integration tests cover `zte run` and `zte read`
- [ ] Tests precede implementation; [P] used only for independent files
- [ ] Documentation updated to match CLI and payload outputs

