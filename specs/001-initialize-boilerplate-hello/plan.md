# Implementation Plan: Initialize Boilerplate Hello World

**Branch**: `001-initialize-boilerplate-hello` | **Date**: 2025-10-06 | **Spec**: [/specs/001-initialize-boilerplate-hello/spec.md](/specs/001-initialize-boilerplate-hello/spec.md)
**Input**: Feature specification from `/specs/001-initialize-boilerplate-hello/spec.md`

## Execution Flow (/plan command scope)
```
1. Load feature spec from Input path
   → If not found: ERROR "No feature spec at {path}"
2. Fill Technical Context (scan for NEEDS CLARIFICATION)
   → Detect Project Type from file system structure or context (web=frontend+backend, mobile=app+api)
   → Set Structure Decision based on project type
3. Fill the Constitution Check section based on the content of the constitution document.
4. Evaluate Constitution Check section below
   → If violations exist: Document in Complexity Tracking
   → If no justification possible: ERROR "Simplify approach first"
   → Update Progress Tracking: Initial Constitution Check
5. Execute Phase 0 → research.md
   → If NEEDS CLARIFICATION remain: ERROR "Resolve unknowns"
6. Execute Phase 1 → contracts, data-model.md, quickstart.md, agent-specific template file (e.g., `CLAUDE.md` for Claude Code, `.github/copilot-instructions.md` for GitHub Copilot, `GEMINI.md` for Gemini CLI, `QWEN.md` for Qwen Code, or `AGENTS.md` for all other agents).
7. Re-evaluate Constitution Check section
   → If new violations: Refactor design, return to Phase 1
   → Update Progress Tracking: Post-Design Constitution Check
8. Plan Phase 2 → Describe task generation approach (DO NOT create tasks.md)
9. STOP - Ready for /tasks command
```

**IMPORTANT**: The /plan command STOPS at step 7. Phases 2-4 are executed by other commands:
- Phase 2: /tasks command creates tasks.md
- Phase 3-4: Implementation execution (manual or via tools)

## Summary
Bootstrap a Python-based `zte` CLI hello-world that runs `zte run` with mocked modem & MQTT interactions, logs via standard logging, exposes Click-powered help/flags, and ships TDD scaffolding demonstrating mocked REST responses and future human-in-the-loop device captures.

## Technical Context
**Language/Version**: Python 3.12 (uv-managed "python stable")  
**Primary Dependencies**: uv (package manager/runtime), gmqtt (MQTT client), click (CLI), standard logging module  
**Storage**: Local filesystem only (configuration + log file)  
**Testing**: pytest with responses/httpx mocking for REST stubs & local fixtures  
**Target Platform**: Linux host running the modem daemon on a LAN  
**Project Type**: single (CLI service + supporting modules)  
**Performance Goals**: CLI startup < 1s; mocked daemon loop emits initial log within 2s  
**Constraints**: Offline/local network only; ensure log file writable path configurable  
**Scale/Scope**: Single ZTE MC888 Ultra modem per daemon instance; dev-oriented hello world

## Constitution Check
*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Telemetry completeness**: Plan documents how mock modem fixtures mirror key REST fields and flags remaining attributes for backlog coverage updates in research.md.
- **Local network enforcement**: Mocked hello world keeps modem + MQTT endpoints as local placeholders and documents prohibition on public endpoints in quickstart.md.
- **Deterministic messaging**: Design specifies placeholder MQTT payload schema in contracts/ and commits to version tags even for mocks to prevent drift.
- **Documentation parity**: Quickstart.md + markdown references will capture CLI usage, mock modem catalog, and MQTT placeholders per constitution.
- **Operational surface**: CLI design covers `zte run` daemon + `zte read` diagnostics with logging, exit codes, and sample systemd/foreground usage guidance.

## Project Structure

### Documentation (this feature)
```
specs/001-initialize-boilerplate-hello/
├── plan.md              # This file (/plan command output)
├── research.md          # Phase 0 output (/plan command)
├── data-model.md        # Phase 1 output (/plan command)
├── quickstart.md        # Phase 1 output (/plan command)
├── contracts/           # Phase 1 output (/plan command)
└── tasks.md             # Phase 2 output (/tasks command - NOT created by /plan)
```

### Source Code (repository root)
```
src/
└── zte_daemon/
    ├── __init__.py
    ├── cli.py
    ├── config.py
    ├── logging_setup.py
    ├── modem/
    │   ├── __init__.py
    │   └── mock_client.py
    └── mqtt/
        ├── __init__.py
        └── mock_publisher.py

tests/
├── unit/
│   ├── test_cli_help.py
│   ├── test_daemon_flow.py
│   └── test_modem_mock.py
├── integration/
│   └── test_hello_world_daemon.py
└── contract/
    └── test_mqtt_placeholder_schema.py
```

**Structure Decision**: Single-project layout under `src/zte_daemon` with mirrored `tests` directories to keep CLI, modem mock, and MQTT mock modules organized for uv/pytest discovery.

## Phase 0: Outline & Research
1. **Extract unknowns from Technical Context** above:
   - Validate Python 3.12 availability under uv default "python stable" channel.
   - Confirm gmqtt mocking patterns for offline development.
   - Determine best practice for capturing real modem responses to seed fixtures.

2. **Generate and dispatch research agents**:
   ```
   Research uv-managed Python stability channel and version pinning for CLI daemons.
   Research gmqtt usage patterns for mocked brokers and offline testing.
   Research workflow for recording ZTE MC888 Ultra REST responses (curl capture) and replaying in tests.
   ```

3. **Consolidate findings** in `research.md` using format:
   - Decision: Selected approach for uv pinning, gmqtt mocks, capture workflow.
   - Rationale: Why each choice aligns with constitution + spec.
   - Alternatives considered: Mention rejected options (e.g., paho-mqtt, manual HTTP mocks).

**Output**: research.md with all identified unknowns resolved.

## Phase 1: Design & Contracts
*Prerequisites: research.md complete*

1. **Extract entities from feature spec** → `data-model.md`:
   - Entities: CLI Command (`zte run`/`zte read`), ModemTelemetrySnapshot, MQTTPlaceholderMessage, LogEvent.
   - Fields & validation: host configs, credentials, metric names, payload schema, log levels.

2. **Generate API contracts** from functional requirements:
   - CLI interface documented in `contracts/cli-help.md` (Click help snapshot).
   - Mock modem REST responses captured in `contracts/modem/mock-status.json`.
   - MQTT placeholder payload defined in `contracts/mqtt/hello-world-message.json` with schema notes.

3. **Generate contract tests** from contracts:
   - `tests/contract/test_cli_help.py` asserts CLI help matches spec.
   - `tests/contract/test_mqtt_placeholder_schema.py` validates payload structure against contract.
   - `tests/contract/test_modem_mock_contract.py` checks mock REST fixtures align with recorded responses.

4. **Extract test scenarios** from user stories:
   - Integration scenario for running `zte run` with mocked modem + MQTT verifying logs and exit code.
   - CLI scenario for `zte read RSRP` and `zte read Provider` using fixtures.
   - Edge-case scenario for unreachable broker raising friendly warning.

5. **Update agent file incrementally** (O(1) operation):
   - Run `.specify/scripts/bash/update-agent-context.sh codex` to sync new tech references (uv, gmqtt, Click, pytest) into AGENTS.md.

**Output**: data-model.md, /contracts/* assets, failing contract tests, quickstart.md, updated AGENTS.md snapshot.

## Phase 2: Task Planning Approach
*This section describes what the /tasks command will do - DO NOT execute during /plan*

**Task Generation Strategy**:
- Use `research.md`, `data-model.md`, contracts, and quickstart to enumerate TDD steps.
- Derive tasks for setting up uv project scaffolding, CLI commands, mocks, and logging.
- Ensure tasks cover documentation updates mandated by constitution (quickstart, markdown trails).

**Ordering Strategy**:
- Start with environment setup + uv configuration.
- Write contract tests (CLI help, modem fixtures, MQTT message) before implementing modules.
- Implement mock modem + MQTT modules, then CLI command, then integration flow.
- Finalize documentation tasks (quickstart, logging explanation), followed by test execution + lint.

**Estimated Output**: 18-22 ordered tasks with [P] markers for parallelizable unit test creation vs documentation updates.

**IMPORTANT**: This phase is executed by the /tasks command, NOT by /plan

## Phase 3+: Future Implementation
*These phases are beyond the scope of the /plan command*

**Phase 3**: Task execution (/tasks command creates tasks.md)  
**Phase 4**: Implementation (execute tasks.md following constitutional principles)  
**Phase 5**: Validation (run tests, execute quickstart.md, performance validation)

## Complexity Tracking
*Fill ONLY if Constitution Check has violations that must be justified*

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| _None_ | — | — |

## Progress Tracking
*This checklist is updated during execution flow*

**Phase Status**:
- [x] Phase 0: Research complete (/plan command)
- [x] Phase 1: Design complete (/plan command)
- [x] Phase 2: Task planning complete (/plan command - describe approach only)
- [ ] Phase 3: Tasks generated (/tasks command)
- [ ] Phase 4: Implementation complete
- [ ] Phase 5: Validation passed

**Gate Status**:
- [x] Initial Constitution Check: PASS
- [x] Post-Design Constitution Check: PASS
- [x] All NEEDS CLARIFICATION resolved
- [x] Complexity deviations documented

---
*Based on Constitution v1.0.0 - See `/memory/constitution.md`*
