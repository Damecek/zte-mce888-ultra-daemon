# Tasks: [FEATURE NAME]

**Input**: Design documents from `/specs/[###-feature-name]/`
**Prerequisites**: plan.md (required), research.md, data-model.md, contracts/

## Execution Flow (main)
```
1. Load plan.md from feature directory
   → If not found: ERROR "No implementation plan found"
   → Extract: tech stack, libraries, structure
2. Load optional design documents:
   → data-model.md: Extract telemetry/catalog entries → polling tasks
   → contracts/: Each file → modem or MQTT contract test task
   → research.md: Extract decisions → setup tasks
3. Generate tasks by category:
   → Setup: project init, dependencies, linting
   → Telemetry: modem HTTP contracts, polling loops
   → MQTT Messaging: topic schemas, publisher logic
   → CLI & Operations: commands, diagnostics, service wiring
   → Documentation: Markdown updates, runbooks, schema notes
   → Validation: integration tests, observability, release checks
4. Apply task rules:
   → Different files = mark [P] for parallel
   → Same file = sequential (no [P])
   → Prefer tests early and include modem/MQTT diagnostics; ensure coverage targets
5. Number tasks sequentially (T001, T002...)
6. Generate dependency graph
7. Create parallel execution examples
8. Validate task completeness:
   → All modem REST contracts have tests?
   → All telemetry attributes and MQTT topics have implementation coverage?
   → All required documentation and CLI/operations deliverables captured?
9. Return: SUCCESS (tasks ready for execution)
```

## Format: `[ID] [P?] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- Include exact file paths in descriptions

## Path Conventions
- **Single project**: `src/`, `tests/` at repository root
- **Web app**: `backend/src/`, `frontend/src/`
- **Mobile**: `api/src/`, `ios/src/` or `android/src/`
- Paths shown below assume single project - adjust based on plan.md structure

## Phase 3.1: Setup
- [ ] T001 Create project structure per implementation plan (e.g., `src/telemetry`, `src/mqtt`, `src/cli`, `docs/`)
- [ ] T002 Initialize runtime environment and dependency management
- [ ] T003 [P] Configure linting, formatting, and CI entrypoints for Linux target

## Phase 3.2: Tests & Coverage
**Goal: Add/adjust tests for new behavior and maintain/raise coverage targets**
- [ ] T004 [P] Contract test modem REST attribute fetch in `tests/contract/test_modem_attributes.py`
- [ ] T005 [P] Contract test modem session handling and authentication renewal in `tests/contract/test_modem_session.py`
- [ ] T006 [P] MQTT payload schema test in `tests/contract/test_mqtt_payloads.py`
- [ ] T007 [P] Integration test polling-to-publish loop in `tests/integration/test_poll_to_mqtt.py`
- [ ] T008 Integration test CLI diagnostics command in `tests/integration/test_cli_status.py`

## Phase 3.3: Core Implementation (ONLY after tests are failing)
<!-- Implementation may proceed when appropriate; tests should accompany changes to maintain coverage targets. -->
- [ ] T009 [P] Implement modem attribute poller in `src/telemetry/zte_mc888.py`
- [ ] T010 [P] Build MQTT publisher with deterministic topic map in `src/mqtt/publisher.py`
- [ ] T011 Wire telemetry-to-MQTT pipeline scheduler in `src/pipeline/dispatcher.py`
- [ ] T012 Implement CLI command group in `src/cli/main.py`
- [ ] T013 Add configuration loader and validation in `src/config/loader.py`
- [ ] T014 Implement structured logging and health signaling in `src/observability/logger.py`

## Phase 3.4: Integration
- [ ] T015 Wire CLI diagnostics to runtime status endpoints
- [ ] T016 Validate local network constraints and block disallowed endpoints
- [ ] T017 Exercise MQTT connectivity against local broker (publish/subscribe loopback)
- [ ] T018 Capture modem credential management (secure storage, refresh cadence)

## Phase 3.5: Polish
- [ ] T019 [P] Unit tests for configuration edge cases in `tests/unit/test_config_validation.py`
- [ ] T020 Performance tests for polling cadence and publish latency budgets
- [ ] T021 [P] Update Markdown docs (`docs/attributes.md`, `docs/mqtt.md`, `docs/cli.md`)
- [ ] T022 Produce operator runbook (`docs/operations.md`) with validation checklist
- [ ] T023 Run manual verification script and capture sample MQTT payloads

## Dependencies
- Contract and integration tests (T004-T008) precede implementation tasks (T009-T014)
- Telemetry poller (T009) must land before pipeline wiring (T011) and network enforcement (T016)
- Configuration loader (T013) blocks diagnostics and validation tasks (T015-T020)
- Documentation and runbooks (T021-T022) depend on finalized schemas and CLI outputs

## Parallel Example
```
# Launch contract-focused tasks together (different files):
Task: "Contract test modem REST attribute fetch in tests/contract/test_modem_attributes.py"
Task: "Contract test modem session handling in tests/contract/test_modem_session.py"
Task: "MQTT payload schema test in tests/contract/test_mqtt_payloads.py"
Task: "Integration test CLI diagnostics command in tests/integration/test_cli_status.py"
```

## Notes
- [P] tasks = different files, no dependencies
- Verify tests fail before implementing
- Attach documentation updates alongside code
- Commit after each task
- Avoid: vague tasks, same file conflicts

## Task Generation Rules
*Applied during main() execution*

1. **From Contracts**:
   - Each modem REST contract file → contract test task [P]
   - Each MQTT schema definition → payload validation and publisher task
   
2. **From Telemetry Catalog**:
   - Each attribute or measurement → polling implementation task [P]
   - Derived metrics or status messages → pipeline aggregation tasks
   
3. **From CLI & Operations Stories**:
   - Each CLI requirement → command implementation and help text update
   - Each operational scenario → diagnostics test or runbook task

4. **Ordering**:
   - Setup → Tests → Telemetry → MQTT → CLI & Config → Documentation/Validation
   - Dependencies block parallel execution

## Validation Checklist
*GATE: Checked by main() before returning*

- [ ] All modem REST contracts have corresponding test tasks
- [ ] All telemetry attributes and MQTT topics have implementation coverage
- [ ] Documentation and runbook updates are scheduled
- [ ] Coverage targets are met; high-risk paths have tests
- [ ] Parallel tasks are independent and specify exact file paths
- [ ] No task modifies the same file as another [P] task
