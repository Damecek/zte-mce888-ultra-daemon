# Feature Specification: ZTE Modem REST Metrics & Discover CLI

**Feature Branch**: `002-we-have-boilerplate`  
**Created**: 2025-10-06  
**Status**: Draft  
**Input**: User description: "we have boilerplate done, now it is time to start implementing real stuf. in js_implementation.js is located javascript script which loggins to the modem frontend on 192.168.0.1/index.html and gathers and displays all possible metrics and some additinal features. Right now we are interested in implementing communication with the device through rest api, getting metrics. the js_implementation.js should guide you, we should reimplement it in this application. do not forget on tdd and mocks, those should be possible to implement based on the script. inputs to this features should be the host ip together with password, there could be more we are not avare of right now. use click to set those inputs. automated test runs should be incorporated in the finalization of each task. be prepared to include more endpoints in the future, for example goform/goform_get_cmd_process?isTest=false&cmd=lan_station_list. create a new subcommand `zte discover --path=goform/goform_get_cmd_process?isTest=false&cmd=lan_station_list --payload=<payload>` or similar, which aims to easily get results from defined endpoint, this then can be used for examples of results used in mocking of the device reponses"

## Execution Flow (main)
```
1. Parse user description from Input
   → If empty: ERROR "No feature description provided"
2. Extract key concepts from description
   → Identify: actors, actions, data, constraints
   → Map modem telemetry attributes and MQTT delivery expectations tied to the feature
   → Capture local network topology assumptions (modem, daemon host, broker)
3. For each unclear aspect:
   → Mark with [NEEDS CLARIFICATION: specific question]
   → Flag missing telemetry attribute definitions or undocumented MQTT topics
4. Fill User Scenarios & Testing section
   → If no clear user flow: ERROR "Cannot determine user scenarios"
5. Generate Functional Requirements
   → Each requirement must be testable
   → Mark ambiguous requirements
   → Include documentation deliverables (Markdown updates, schema revisions) triggered by the feature
6. Identify Key Entities (if data involved)
7. Run Review Checklist
   → If any [NEEDS CLARIFICATION]: WARN "Spec has uncertainties"
   → If implementation details found: ERROR "Remove tech details"
8. Return: SUCCESS (spec ready for planning)
```

---

## ⚡ Quick Guidelines
- ✅ Focus on WHAT users need and WHY
- ❌ Avoid HOW to implement (no tech stack, APIs, code structure)
- 👥 Written for business stakeholders, not developers

### Section Requirements
- **Mandatory sections**: Must be completed for every feature
- **Optional sections**: Include only when relevant to the feature
- When a section doesn't apply, remove it entirely (don't leave as "N/A")

### For AI Generation
When creating this spec from a user prompt:
1. **Mark all ambiguities**: Use [NEEDS CLARIFICATION: specific question] for any assumption you'd need to make
2. **Don't guess**: If the prompt doesn't specify something (e.g., "login system" without auth method), mark it
3. **Think like a tester**: Every vague requirement should fail the "testable and unambiguous" checklist item
4. **Common underspecified areas**:
   - User types and permissions
   - Data retention/deletion policies  
   - Performance targets and scale
   - Error handling behaviors
   - Integration requirements
   - Security/compliance needs

---

## Clarifications

### Session 2025-10-06
- Q: What is the source of truth for modem authentication details and how should missing details be handled? → A: Use `js_implementation.js` as the definitive reference for the REST auth flow. If anything remains unclear, provide the human with precise steps to extract the required info and have them report back.
- Q: Which metrics are in scope to retrieve and document? → A: All metrics rendered by the JS when inserted into the modem DOM (document in Markdown): LTE (B20) RSRP1, SINR1, RSRP2, SINR2, RSRP3, SINR3, RSRP4, SINR4, RSRQ, RSSI, EARFCN, PCI, BW; 5G (n28) RSRP1, RSRP2, SINR, ARFCN, PCI, BW; PROVIDER; CELL; NGBR entries (e.g., 354/389/39/314 with RSRP/RSRQ); CONNECTION; BANDS; WAN IP; TEMP (A/M/P).
- Q: How should HTTP method selection work for the `zte discover` command? → A: Add `--method`. Default to GET when no `--payload` is provided; default to POST when `--payload` is provided; allow explicit override via `--method`.
- Q: How should discover inputs/outputs be shared and returned? → A: Provide a shared folder of Markdown files defining inputs to the discover command together with output payload; the command should return this file and support a `--target-file` flag.
 - Q: Do logs need redaction of sensitive fields? → A: No redaction required; the CLI runs on a local network and users are responsible for not exposing logs.
 - Q: Which folder path should be used for discover example Markdown files? → A: docs/discover
 - Q: Does this specification replace the hello-world baseline and require removal of hello-world code/docs? → A: Yes. This feature supersedes `specs/001-initialize-boilerplate-hello/spec.md`; remove hello-world behavior (greetings/mocks/docs/tests) but RETAIN the CLI command names `zte run` and `zte read` with updated real functionality.
 - Q: Should the existing commands `zte run` and `zte read` be persisted? → A: Yes. Persist both; `zte run` remains the daemon entry; `zte read <metric>` performs a one-off REST read of the specified metric.
 - Q: How should authentication handle username? → A: Password only (no username input).
 - Q: Which default modem host/IP should be used? → A: No default; require `--host`.
- Q: How should `--payload` be encoded and sent by default? → A: JSON body with `Content-Type: application/json`.
 - Q: Which HTTP client library should be used? → A: httpx.
 - Q: How should the `zte discover` subcommand be registered? → A: As a separate command module (`zte discover`) under the CLI commands.

## User Scenarios & Testing *(mandatory)*

### Primary User Story
An operator uses a local CLI to connect to a ZTE MC888 modem on the LAN, authenticates with the modem’s web frontend credentials, and retrieves device metrics via REST endpoints. The operator can also run a "discover" command to query any supported endpoint by path (and optional payload) to view raw responses, which are then used as examples for test mocking.

### Acceptance Scenarios
1. Given a reachable modem at a specified host IP and valid credentials, when the user runs the CLI to fetch metrics, then the system authenticates, retrieves metrics from the modem’s REST endpoints, and displays results without exposing the password.
2. Given a path such as `goform/goform_get_cmd_process?isTest=false&cmd=lan_station_list`, when the user runs `zte discover --path=<path>` with an optional `--payload`, then the system returns the raw response (e.g., JSON/text) and indicates success or error via exit code and message.
3. Given invalid credentials, when the user runs any command requiring authentication, then the system reports an authentication error, does not display sensitive data, and exits with a non-zero status.
4. Given the modem is unreachable (timeout or DNS failure), when a request is attempted, then the system reports a network connectivity error and exits with a non-zero status.
5. Given malformed or unexpected responses from the modem, when parsing is attempted, then the system reports a clear parsing/format error and suggests using `zte discover` to inspect the raw payload.
6. Given a `zte discover` call without `--payload`, then the request uses GET unless `--method` overrides it; with `--payload`, default to POST unless overridden by `--method`, and encode payload as JSON with `Content-Type: application/json`.
7. Given the repository previously contained hello-world scaffolding, when this feature is completed, then the `hello` greeting output and hello-world docs/tests are removed (e.g., `tests/integration/test_hello_world_flow.py`, README hello references), while the CLI commands `zte run` and `zte read` still exist and operate with real REST integration.
8. Given `zte read <metric>` with a valid metric key and required flags (`--host`, `--password`), when executed, then the CLI returns the metric value and exits 0; for an unknown metric, it exits non-zero with a clear error.
9. Given any command requiring authentication, when the user runs the CLI, then it never prompts for or requires a username and authenticates using the password-only flow.
10. Given the CLI is invoked without specifying `--host`, when any command runs, then the CLI errors with a clear message that the host is required and exits non-zero.

### Edge Cases
- Session expiry or CSRF/token rotation during a multi-call flow → system should detect unauthenticated state and retry login once before failing. [NEEDS CLARIFICATION: exact auth/session mechanism]
- Non-JSON responses from endpoints typically returning JSON → system should surface raw content via discover and provide a clear message.
- Captive portal or modem in setup mode → system should detect non-standard landing pages and report unsupported state.
- Rate limiting or temporary modem overload → system should back off briefly and report transient failure if limits persist. [NEEDS CLARIFICATION: modem throttling behavior]
- Password containing special characters → system must handle safely via CLI input without leaking or shell interpolation issues.
 - Discover file outputs unavailable (invalid path or missing folder) → system should error clearly, not create nested directories implicitly, and suggest verifying `docs/discover` exists.

## Requirements *(mandatory)*

### Functional Requirements
- **FR-001**: The CLI MUST allow users to specify modem host/IP and password as inputs for all commands requiring authentication; host/IP input is REQUIRED (no default), and no username input is required.
- **FR-002**: The system MUST authenticate against the modem’s frontend-compatible flow before requesting protected endpoints. [NEEDS CLARIFICATION: exact login endpoint, token/cookie, hashing/salting requirements derived from `js_implementation.js`]
- **FR-003**: The system MUST retrieve modem metrics via REST endpoints as guided by `js_implementation.js`, starting with a minimum viable set to confirm connectivity and parsing. [NEEDS CLARIFICATION: initial metrics list]
- **FR-004**: The CLI MUST provide a subcommand `zte discover` with options `--path=<relative-endpoint-path>` and optional `--payload=<data>` to fetch and print the raw response body.
- **FR-005**: The discover command MUST support future endpoints without code changes by passing through arbitrary endpoint paths (and payloads if accepted by the modem).
- **FR-006**: The system MUST include test-driven development (TDD) coverage; all HTTP interactions in tests MUST be mocked using sample responses informed by `js_implementation.js` and discover outputs.
- **FR-007**: The system MUST surface clear error messages and appropriate exit codes for authentication failures, connectivity issues, and unexpected response formats.
- **FR-008**: Automated tests MUST run as part of feature completion, with a local test runner command documented for developers.
- **FR-009**: The system SHOULD capture example responses (snapshots) from discover runs for reuse in mocks. [NEEDS CLARIFICATION: storage location/format and update workflow]
- **FR-010**: The system SHOULD provide operational logging sufficient to troubleshoot connectivity/auth issues; redaction is not required per local-only usage policy.
- **FR-011**: The `zte discover` command MUST support a `--method` option with defaults: GET when no `--payload` provided, POST when `--payload` provided; `--method` explicitly overrides defaults.
- **FR-012**: The `zte discover` command MUST support `--target-file` to write a Markdown file containing the request inputs and output payload, and print the path to this file.
- **FR-013**: A shared Markdown folder MUST exist for discover input/output examples used for mocking at `docs/discover`.

- **FR-014**: Remove the hello-world baseline: delete or refactor away hello-world tests, mocks, greetings, and documentation and `tests/integration/test_hello_world_flow.py` while RETAINING the CLI command names `zte run` and `zte read` with updated semantics.
- **FR-015**: By default, the CLI and client MUST encode `--payload` as JSON and send with header `Content-Type: application/json`.
- **FR-016**: The CLI MUST continue to expose `zte run` as the daemon entrypoint (executing the real REST-driven workflow) and `zte read <metric>` for one-off interactive reads of a specific metric via REST.

### Key Entities *(include if feature involves data)*
- **Modem Session**: Represents authenticated state with the modem (e.g., cookies/tokens, CSRF if applicable); attributes: authenticated flag, session identifiers, expiry. [NEEDS CLARIFICATION: concrete auth artifacts]
- **Endpoint Request**: A single request definition with relative path, optional payload, expected response type (raw/JSON), and error mapping.
- **Metric Snapshot**: A collection of key/value modem metrics obtained from one or more endpoints; includes timestamp and source host.
 - **Discover Example File**: Markdown artifact stored under `docs/discover` containing endpoint path, method, payload, and captured response; used as fixtures/mocks.

---

## Review & Acceptance Checklist
*GATE: Automated checks run during main() execution*

### Content Quality
- [ ] No implementation details (languages, frameworks, APIs)
- [ ] Focused on user value and business needs
- [ ] Written for non-technical stakeholders
- [ ] All mandatory sections completed

### Requirement Completeness
- [ ] No [NEEDS CLARIFICATION] markers remain
- [ ] Requirements are testable and unambiguous  
- [ ] Success criteria are measurable
- [ ] Scope is clearly bounded
- [ ] Dependencies and assumptions identified
- [ ] Telemetry coverage, MQTT schema impact, documentation updates, and CLI/operational implications are explicitly addressed

---

## Execution Status
*Updated by main() during processing*

- [ ] User description parsed
- [ ] Key concepts extracted
- [ ] Ambiguities marked
- [ ] User scenarios defined
- [ ] Requirements generated
- [ ] Entities identified
- [ ] Review checklist passed

---
