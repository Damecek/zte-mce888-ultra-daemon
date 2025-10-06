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
- [ ] T001 Create source and test structure per plan
  - Create directories: `/Users/adam/IdeaProjects/zte-mc888-ultra-deamon/src/{models,services,cli,lib}` and `/Users/adam/IdeaProjects/zte-mc888-ultra-deamon/tests/{contract,integration,unit,fixtures}`
  - Add `.gitkeep` files where needed
- [ ] T002 Decide HTTP client and record in research
  - Update decision in `/Users/adam/IdeaProjects/zte-mc888-ultra-deamon/specs/002-we-have-boilerplate/research.md` (choose `requests` or `httpx` with rationale)
  - Add dependency in `/Users/adam/IdeaProjects/zte-mc888-ultra-deamon/pyproject.toml`
- [ ] T003 [P] Ensure docs/discover exists for example files
  - Create directory: `/Users/adam/IdeaProjects/zte-mc888-ultra-deamon/docs/discover`

## Phase 3.2: Tests First (TDD) — must fail before implementation
- [ ] T004 [P] Contract test: Authentication flow (from js_implementation.js)
  - Create `/Users/adam/IdeaProjects/zte-mc888-ultra-deamon/tests/contract/test_auth_flow.py`
  - Mock login endpoint, cookies/tokens, and a protected GET to assert session handling
- [ ] T005 [P] Contract test: Discover default method = GET when no payload
  - Create `/Users/adam/IdeaProjects/zte-mc888-ultra-deamon/tests/contract/test_discover_default_get.py`
  - Use Click CliRunner to invoke `zte discover --path ...` and assert GET used
- [ ] T006 [P] Contract test: Discover default method = POST when payload present
  - Create `/Users/adam/IdeaProjects/zte-mc888-ultra-deamon/tests/contract/test_discover_default_post.py`
  - Assert POST used unless `--method` overrides
- [ ] T007 [P] Contract test: `--target-file` writes Markdown under docs/discover
  - Create `/Users/adam/IdeaProjects/zte-mc888-ultra-deamon/tests/contract/test_discover_target_file.py`
  - Assert file content includes request (path, method, payload) and response blocks
- [ ] T008 Integration test: CLI discover end-to-end behavior and exit codes
  - Create `/Users/adam/IdeaProjects/zte-mc888-ultra-deamon/tests/integration/test_cli_discover.py`
  - Cover unreachable host, auth failure, success with JSON body
- [ ] T009 [P] Unit test: ZTE client error mapping and timeouts
  - Create `/Users/adam/IdeaProjects/zte-mc888-ultra-deamon/tests/unit/test_zte_client_errors.py`
  - Assert clear exceptions for timeouts, 401/403, parse errors
- [ ] T010 [P] Unit test: Metrics documentation completeness list exists
  - Create `/Users/adam/IdeaProjects/zte-mc888-ultra-deamon/tests/unit/test_metrics_docs.py`
  - Ensure `/Users/adam/IdeaProjects/zte-mc888-ultra-deamon/docs/metrics.md` includes all metrics from Clarifications

## Phase 3.3: Core Implementation (only after tests fail)
- [ ] T011 Implement ZTE REST client
  - Add `/Users/adam/IdeaProjects/zte-mc888-ultra-deamon/src/services/zte_client.py`
  - Provide: constructor(host), `login(password, ...)`, `request(path, method, payload=None, expects="json|text")`
  - Manage cookies/tokens per `js_implementation.js`
- [ ] T012 Implement CLI: `zte discover`
  - Add `/Users/adam/IdeaProjects/zte-mc888-ultra-deamon/src/cli/zte.py`
  - Click group `zte`; subcommand `discover` with `--host`, `--password`, `--path`, `--payload`, `--method`, `--target-file`
  - Default GET if no payload; POST if payload; `--method` overrides
- [ ] T013 Implement Markdown writer for discover outputs
  - Add `/Users/adam/IdeaProjects/zte-mc888-ultra-deamon/src/lib/markdown_io.py`
  - Function `write_discover_example(target_file, host, path, method, payload, response)`
- [ ] T014 Wire logging per policy (no redaction)
  - Add `/Users/adam/IdeaProjects/zte-mc888-ultra-deamon/src/lib/logging_setup.py` and integrate into CLI and services
- [ ] T015 Define metric snapshot structures
  - Add `/Users/adam/IdeaProjects/zte-mc888-ultra-deamon/src/models/metrics.py` aligned with data-model.md
- [ ] T016 Document metrics in Markdown
  - Add `/Users/adam/IdeaProjects/zte-mc888-ultra-deamon/docs/metrics.md` enumerating LTE/5G metrics, provider/cell, neighbors, connection, bands, WAN IP, temps (A/M/P)

## Phase 3.4: Integration
- [ ] T017 Enforce method defaulting and overrides in CLI and client
  - Verify behaviors against tests T005-T006
- [ ] T018 Implement clear error messages and exit codes
  - Map auth/network/parse errors to non-zero exits in CLI
- [ ] T019 Add single retry on session expiry
  - Detect unauthenticated response; retry login once then fail
- [ ] T020 Add snapshot capture helper for mocks
  - Add `/Users/adam/IdeaProjects/zte-mc888-ultra-deamon/src/lib/snapshots.py` to persist example payloads optionally alongside docs/discover

## Phase 3.5: Polish
- [ ] T021 [P] Seed example discover files
  - Create `/Users/adam/IdeaProjects/zte-mc888-ultra-deamon/docs/discover/lan_station_list.md` with sample
- [ ] T022 [P] Update CLI docs
  - Add `/Users/adam/IdeaProjects/zte-mc888-ultra-deamon/docs/cli.md` documenting `zte discover` usage and options
- [ ] T023 [P] Lint and static checks
  - Run `ruff check .` at repo root: `/Users/adam/IdeaProjects/zte-mc888-ultra-deamon`
- [ ] T024 [P] Final test run
  - Run `pytest` at repo root and ensure all tests pass
- [ ] T025 [P] README and quickstart updates
  - Update `/Users/adam/IdeaProjects/zte-mc888-ultra-deamon/README.md` to link to docs and include examples
- [ ] T026 [P] Record auth contract details
  - Extract from `/Users/adam/IdeaProjects/zte-mc888-ultra-deamon/js_implementation.js` and update `/Users/adam/IdeaProjects/zte-mc888-ultra-deamon/specs/002-we-have-boilerplate/contracts/README.md`

## Dependencies
- T004–T010 (tests) precede T011–T016 (implementation)
- T011 (client) precedes T012 (CLI) and T017–T019 (integration behaviors)
- T013 (Markdown writer) needed before T007 and T012 pass
- T016 (metrics docs) required before T010 passes

## Parallel Execution Example
```
# Run contract-focused tests in parallel once created (different files):
Task: "pytest /Users/adam/IdeaProjects/zte-mc888-ultra-deamon/tests/contract/test_auth_flow.py -q"
Task: "pytest /Users/adam/IdeaProjects/zte-mc888-ultra-deamon/tests/contract/test_discover_default_get.py -q"
Task: "pytest /Users/adam/IdeaProjects/zte-mc888-ultra-deamon/tests/contract/test_discover_default_post.py -q"
Task: "pytest /Users/adam/IdeaProjects/zte-mc888-ultra-deamon/tests/contract/test_discover_target_file.py -q"
```

## Validation Checklist
- [ ] All modem REST contracts have corresponding test tasks
- [ ] All targeted modem metrics are documented in docs/metrics.md
- [ ] CLI discover behaviors covered by tests (defaults, overrides, target-file)
- [ ] All tests precede implementation
- [ ] Parallel tasks are independent and include absolute file paths
- [ ] No two [P] tasks modify the same file

