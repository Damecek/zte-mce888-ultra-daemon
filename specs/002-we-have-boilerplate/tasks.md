# Tasks: ZTE Modem REST Metrics & Discover CLI

**Input**: Design documents from `/specs/002-we-have-boilerplate/`
**Prerequisites**: plan.md (required), research.md, data-model.md, contracts/

## Execution Flow (main)
```
1. Load plan.md and extract tech stack and structure
2. Load optional design docs: data-model.md, contracts/, research.md, quickstart.md
3. Generate tasks by category (Setup → Tests → Core → Integration → Polish)
4. Apply task rules (tests first, [P] for independent files)
5. Number tasks sequentially (T001, T002...)
6. Document dependencies and parallel examples
```

## Format: `[ID] [P?] Description`
- [P] = Can run in parallel (different files, no dependencies)
- Include absolute file paths in descriptions

## Phase 3.1: Setup
- [X] T001 Create source and test structure per plan
  - Create directories: `/Users/adam/IdeaProjects/zte-mc888-ultra-deamon/src/{models,services,cli,lib}` and `/Users/adam/IdeaProjects/zte-mc888-ultra-deamon/tests/{contract,integration,unit,fixtures}`
  - Add `.gitkeep` files where needed
- [X] T002 Decide HTTP client and record in research
  - Update decision in `/Users/adam/IdeaProjects/zte-mc888-ultra-deamon/specs/002-we-have-boilerplate/research.md` (choose `requests` or `httpx` with rationale)
  - Add dependency in `/Users/adam/IdeaProjects/zte-mc888-ultra-deamon/pyproject.toml`
- [X] T003 [P] Ensure docs/discover exists for example files
  - Create directory: `/Users/adam/IdeaProjects/zte-mc888-ultra-deamon/docs/discover`
- [X] T004 Remove hello-world baseline artifacts but retain command names
  - Delete: `/Users/adam/IdeaProjects/zte-mc888-ultra-deamon/tests/integration/test_hello_world_flow.py`
  - Remove hello greeting from: `/Users/adam/IdeaProjects/zte-mc888-ultra-deamon/src/zte_daemon/cli/commands/run.py`
  - Update README title and sections to remove "Hello World" at `/Users/adam/IdeaProjects/zte-mc888-ultra-deamon/README.md`
  - Update project description in `/Users/adam/IdeaProjects/zte-mc888-ultra-deamon/pyproject.toml`
  - Add superseded note to: `/Users/adam/IdeaProjects/zte-mc888-ultra-deamon/specs/001-initialize-boilerplate-hello/spec.md`

## Phase 3.2: Tests First (TDD) — must fail before implementation
- [X] T004 [P] Contract test: Authentication flow (from js_implementation.js)
  - Create `/Users/adam/IdeaProjects/zte-mc888-ultra-deamon/tests/contract/test_auth_flow.py`
  - Mock login endpoint, cookies/tokens, and a protected GET to assert session handling
- [X] T005 [P] Contract test: Discover default method = GET when no payload
  - Create `/Users/adam/IdeaProjects/zte-mc888-ultra-deamon/tests/contract/test_discover_default_get.py`
  - Use Click CliRunner to invoke `zte discover --path ...` and assert GET used
- [X] T006 [P] Contract test: Discover default method = POST when payload present
  - Create `/Users/adam/IdeaProjects/zte-mc888-ultra-deamon/tests/contract/test_discover_default_post.py`
  - Assert POST used unless `--method` overrides
- [X] T007 [P] Contract test: `--target-file` writes Markdown under docs/discover
  - Create `/Users/adam/IdeaProjects/zte-mc888-ultra-deamon/tests/contract/test_discover_target_file.py`
  - Assert file content includes request (path, method, payload) and response blocks
- [X] T008 Integration test: CLI discover end-to-end behavior and exit codes
  - Create `/Users/adam/IdeaProjects/zte-mc888-ultra-deamon/tests/integration/test_cli_discover.py`
  - Cover unreachable host, auth failure, success with JSON body
- [X] T009 [P] Unit test: ZTE client error mapping and timeouts
  - Create `/Users/adam/IdeaProjects/zte-mc888-ultra-deamon/tests/unit/test_zte_client_errors.py`
  - Assert clear exceptions for timeouts, 401/403, parse errors
- [X] T010 [P] Unit test: Metrics documentation completeness list exists
  - Create `/Users/adam/IdeaProjects/zte-mc888-ultra-deamon/tests/unit/test_metrics_docs.py`
  - Ensure `/Users/adam/IdeaProjects/zte-mc888-ultra-deamon/docs/metrics.md` includes all metrics from Clarifications
- [ ] T012 [P] Contract test: Missing `--host` yields clear error and non-zero exit
  - Create `/Users/adam/IdeaProjects/zte-mc888-ultra-deamon/tests/contract/test_missing_host_required.py`
  - Assert both `zte discover` and `zte read` fail without `--host`
- [ ] T013 [P] Contract test: `--payload` JSON encoding and header
  - Create `/Users/adam/IdeaProjects/zte-mc888-ultra-deamon/tests/contract/test_payload_json_header.py`
  - Assert `Content-Type: application/json` and JSON body sent
- [ ] T014 Integration test: `zte read <metric>` success and unknown metric error
  - Create `/Users/adam/IdeaProjects/zte-mc888-ultra-deamon/tests/integration/test_cli_read_metric.py`
  - Use CliRunner with mocked client to return a known metric; assert outputs/exit codes
- [ ] T015 Integration test: `zte run` executes minimal real REST-driven workflow
  - Create `/Users/adam/IdeaProjects/zte-mc888-ultra-deamon/tests/integration/test_cli_run_daemon.py`
  - Assert it performs a fetch cycle, logs status, and exits deterministically in test mode

## Phase 3.3: Core Implementation (only after tests fail)
- [X] T011 Implement ZTE REST client
  - Add `/Users/adam/IdeaProjects/zte-mc888-ultra-deamon/src/services/zte_client.py`
  - Provide: constructor(host), `login(password, ...)`, `request(path, method, payload=None, expects="json|text")`
  - Manage cookies/tokens per `js_implementation.js`
- [X] T012 Implement CLI: `zte discover`
  - Add `/Users/adam/IdeaProjects/zte-mc888-ultra-deamon/src/cli/zte.py`
  - Click group `zte`; subcommand `discover` with `--host`, `--password`, `--path`, `--payload`, `--method`, `--target-file`
  - Default GET if no payload; POST if payload; `--method` overrides
- [X] T013 Implement Markdown writer for discover outputs
  - Add `/Users/adam/IdeaProjects/zte-mc888-ultra-deamon/src/lib/markdown_io.py`
  - Function `write_discover_example(target_file, host, path, method, payload, response)`
- [X] T014 Wire logging per policy (no redaction)
  - Add `/Users/adam/IdeaProjects/zte-mc888-ultra-deamon/src/lib/logging_setup.py` and integrate into CLI and services
- [X] T015 Define metric snapshot structures
  - Add `/Users/adam/IdeaProjects/zte-mc888-ultra-deamon/src/models/metrics.py` aligned with data-model.md
- [X] T016 Document metrics in Markdown
  - Add `/Users/adam/IdeaProjects/zte-mc888-ultra-deamon/docs/metrics.md` enumerating LTE/5G metrics, provider/cell, neighbors, connection, bands, WAN IP, temps (A/M/P)
- [X] T022 Refactor CLI: `zte read` to use REST client
  - Update `/Users/adam/IdeaProjects/zte-mc888-ultra-deamon/src/zte_daemon/cli/commands/read.py` to fetch a specific metric
- [X] T023 Refactor CLI: `zte run` to orchestrate a minimal fetch cycle
  - Update `/Users/adam/IdeaProjects/zte-mc888-ultra-deamon/src/zte_daemon/cli/commands/run.py` to call the REST client (test mode)

## Phase 3.4: Integration
- [X] T017 Enforce method defaulting and overrides in CLI and client
  - Verify behaviors against tests T005-T006
- [X] T018 Implement clear error messages and exit codes
  - Map auth/network/parse errors to non-zero exits in CLI
- [X] T019 Add single retry on session expiry
  - Detect unauthenticated response; retry login once then fail
- [X] T020 Add snapshot capture helper for mocks
  - Add `/Users/adam/IdeaProjects/zte-mc888-ultra-deamon/src/lib/snapshots.py` to persist example payloads optionally alongside docs/discover

## Phase 3.5: Polish
- [X] T021 [P] Seed example discover files
  - Create `/Users/adam/IdeaProjects/zte-mc888-ultra-deamon/docs/discover/lan_station_list.md` with sample
- [X] T022 [P] Update CLI docs
  - Add `/Users/adam/IdeaProjects/zte-mc888-ultra-deamon/docs/cli.md` documenting `zte discover` usage and options
- [X] T023 [P] Lint and static checks
  - Run `ruff check .` at repo root: `/Users/adam/IdeaProjects/zte-mc888-ultra-deamon`
- [X] T024 [P] Final test run
  - Run `pytest` at repo root and ensure all tests pass
- [X] T025 [P] README and quickstart updates
  - Update `/Users/adam/IdeaProjects/zte-mc888-ultra-deamon/README.md` to link to docs and include examples
- [X] T026 [P] Record auth contract details
  - Extract from `/Users/adam/IdeaProjects/zte-mc888-ultra-deamon/js_implementation.js` and update `/Users/adam/IdeaProjects/zte-mc888-ultra-deamon/specs/002-we-have-boilerplate/contracts/README.md`

## Dependencies
- T005–T015 (tests) precede T016–T023 (implementation)
- T016 (client) precedes T017 (CLI) and T024–T026 (integration behaviors)
- T018 (Markdown writer) needed before T008 and T017 pass
- T021 (metrics docs) required before T011 passes
- T022–T023 after client available
- T004 (hello-world removal) before any tests to avoid conflicts

## Parallel Execution Example
```
# Run contract-focused tests in parallel once created (different files):
Task: "pytest /Users/adam/IdeaProjects/zte-mc888-ultra-deamon/tests/contract/test_auth_flow.py -q"
Task: "pytest /Users/adam/IdeaProjects/zte-mc888-ultra-deamon/tests/contract/test_discover_default_get.py -q"
Task: "pytest /Users/adam/IdeaProjects/zte-mc888-ultra-deamon/tests/contract/test_discover_default_post.py -q"
Task: "pytest /Users/adam/IdeaProjects/zte-mc888-ultra-deamon/tests/contract/test_discover_target_file.py -q"
Task: "pytest /Users/adam/IdeaProjects/zte-mc888-ultra-deamon/tests/contract/test_missing_host_required.py -q"
Task: "pytest /Users/adam/IdeaProjects/zte-mc888-ultra-deamon/tests/contract/test_payload_json_header.py -q"
```

## Validation Checklist
- [X] All modem REST contracts have corresponding test tasks
- [X] All targeted modem metrics are documented in docs/metrics.md
- [X] CLI discover behaviors covered by tests (defaults, overrides, target-file)
- [X] All tests precede implementation
- [X] Parallel tasks are independent and include absolute file paths
- [X] No two [P] tasks modify the same file
