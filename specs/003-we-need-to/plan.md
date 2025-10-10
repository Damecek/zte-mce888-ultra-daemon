
# Implementation Plan: MQTT-Driven ZTE Daemon (`zte run`)

**Branch**: `003-we-need-to` | **Date**: 2025-10-10 | **Spec**: /Users/adam/IdeaProjects/zte-mc888-ultra-deamon/specs/003-we-need-to/spec.md
**Input**: Feature specification from `/specs/003-we-need-to/spec.md`

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
- Implement a long-running `zte run` daemon that subscribes to a configurable MQTT root topic and responds to on-demand requests by fetching metrics from the ZTE MC888 router (via existing `zte read` code paths using `services/zte_client.py`) and publishing results back.
- Request pattern: `<root>/<metric>/get` (e.g., `zte/provider/get`) → respond on `<root>/<metric>` (e.g., `zte/provider`).
- Aggregate request: `<root>/lte/get` publishes an object mapping all LTE metrics (as defined in `docs/metrics.md`) to `<root>/lte`.
- Constraints (per clarifications): QoS 0, retain false, reconnect every 5s, plaintext MQTT (no TLS for this feature), sequential handling, treat `--mqtt-topic` as literal (no placeholders), lowercase topic paths, default root `zte`, default port `1883`.

## Technical Context
**Language/Version**: Python 3.12 (uv-managed "python stable")  
**Primary Dependencies**: Click CLI, standard logging, gmqtt (client), pytest, ruff  
**Storage**: N/A (in-memory; optional on-disk fixtures for snapshots)  
**Testing**: pytest (`uv run pytest`) with CI on Linux; ruff lint/format  
**Target Platform**: Linux server (local network), macOS dev  
**Project Type**: single  
**Performance Goals**: Responsive on-demand fetch; typical round-trip under a few seconds; minimal CPU/memory  
**Constraints**: Local-only broker, QoS 0, retain false, plaintext MQTT (no TLS in this feature), reconnect every 5s, sequential request handling, lowercase topics, literal `--mqtt-topic`, default root `zte`, default port 1883  
**Scale/Scope**: Home/office deployments; low message volume; single modem instance  
**Additional Input Arguments**: none provided ($ARGUMENTS empty)

## Constitution Check
*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Telemetry completeness**: Leverage `services/zte_client.py` and `docs/metrics.md`; aggregate `lte/get` publishes all LTE metrics. Track unsupported attributes via docs and backlog entries.
- **Local network enforcement**: Operate only against local modem (default `192.168.0.1`) and local MQTT broker; no cloud endpoints. Document risks if configured otherwise.
- **Deterministic messaging**: Topic and payload contracts defined in `/specs/003-we-need-to/contracts/mqtt.md`; lowercase normalization; no breaking changes to existing metric identifiers.
- **Documentation parity**: Update contracts, quickstart, and data model under `/specs/003-we-need-to/`; reference `docs/metrics.md` and CLI usage.
- **Operational surface**: CLI flags for modem and MQTT; logs distinguish config vs connectivity vs runtime; daemon foreground/background modes.
- **Maintainability**: Keep modules within `services`, `cli`, `models`, `lib`; add docstrings; enforce ruff.
- **Modularity**: Separate MQTT I/O (gmqtt client), telemetry (ZTE client), pipeline (request→fetch→publish), CLI wiring, and config parsing.
- **Testing & coverage**: Extend pytest with contract/integration tests; maintain coverage thresholds in CI.

## Project Structure

### Documentation (this feature)
```
specs/[###-feature]/
├── plan.md              # This file (/plan command output)
├── research.md          # Phase 0 output (/plan command)
├── data-model.md        # Phase 1 output (/plan command)
├── quickstart.md        # Phase 1 output (/plan command)
├── contracts/           # Phase 1 output (/plan command)
└── tasks.md             # Phase 2 output (/tasks command - NOT created by /plan)
```

### Source Code (repository root)
<!--
  ACTION REQUIRED: Replace the placeholder tree below with the concrete layout
  for this feature. Delete unused options and expand the chosen structure with
  real paths (e.g., apps/admin, packages/something). The delivered plan must
  not include Option labels.
-->
```
# [REMOVE IF UNUSED] Option 1: Single project (DEFAULT)
src/
├── models/
├── services/
├── cli/
└── lib/

tests/
├── contract/
├── integration/
└── unit/

# [REMOVE IF UNUSED] Option 2: Web application (when "frontend" + "backend" detected)
backend/
├── src/
│   ├── models/
│   ├── services/
│   └── api/
└── tests/

frontend/
├── src/
│   ├── components/
│   ├── pages/
│   └── services/
└── tests/

# [REMOVE IF UNUSED] Option 3: Mobile + API (when "iOS/Android" detected)
api/
└── [same as backend above]

ios/ or android/
└── [platform-specific structure: feature modules, UI flows, platform tests]
```

**Structure Decision**: [Document the selected structure and reference the real
directories captured above]

## Phase 0: Outline & Research
1. **Extract unknowns from Technical Context** above:
   - For each NEEDS CLARIFICATION → research task
   - For each dependency → best practices task
   - For each integration → patterns task

2. **Generate and dispatch research agents**:
   ```
   For each unknown in Technical Context:
     Task: "Research {unknown} for {feature context}"
   For each technology choice:
     Task: "Find best practices for {tech} in {domain}"
   ```

3. **Consolidate findings** in `research.md` using format:
   - Decision: [what was chosen]
   - Rationale: [why chosen]
   - Alternatives considered: [what else evaluated]

**Output**: research.md with all NEEDS CLARIFICATION resolved

## Phase 1: Design & Contracts
*Prerequisites: research.md complete*

1. **Extract entities from feature spec** → `data-model.md`:
   - Entity name, fields, relationships
   - Validation rules from requirements
   - State transitions if applicable

2. **Generate API contracts** from functional requirements:
   - For each user action → endpoint
   - Use standard REST/GraphQL patterns
   - Output OpenAPI/GraphQL schema to `/contracts/`

3. **Generate contract tests** from contracts:
   - One test file per endpoint
   - Assert request/response schemas
   - Tests must fail (no implementation yet)

4. **Extract test scenarios** from user stories:
   - Each story → integration test scenario
   - Quickstart test = story validation steps

5. **Update agent file incrementally** (O(1) operation):
   - Run `.specify/scripts/bash/update-agent-context.sh codex`
     **IMPORTANT**: Execute it exactly as specified above. Do not add or remove any arguments.
   - If exists: Add only NEW tech from current plan
   - Preserve manual additions between markers
   - Update recent changes (keep last 3)
   - Keep under 150 lines for token efficiency
   - Output to repository root

**Output**: data-model.md, /contracts/*, failing tests, quickstart.md, agent-specific file

## Phase 2: Task Planning Approach
*This section describes what the /tasks command will do - DO NOT execute during /plan*

**Task Generation Strategy**:
- Load `.specify/templates/tasks-template.md` as base
- Generate tasks from Phase 1 design docs (contracts, data model, quickstart)
- Each contract → contract test task [P]
- Each entity → model creation task [P] 
- Each user story → integration test task
- Implementation tasks to make tests pass

**Ordering Strategy**:
- Prefer tests early; ensure coverage targets are met
- Dependency order: Models before services before UI
- Mark [P] for parallel execution (independent files)

**Estimated Output**: 25-30 numbered, ordered tasks in tasks.md

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
 | MQTT TLS omitted in feature | Clarification states plaintext only; local-only broker reduces risk; will add optional TLS in a follow-up | Immediate TLS support would delay feature; broker environments vary and need discovery/testing |


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
*Based on Constitution v1.1.0 - See `/memory/constitution.md`*
