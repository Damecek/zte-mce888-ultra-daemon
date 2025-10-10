<!--
Sync Impact Report
Version change: 1.0.0 → 1.1.0
Modified principles: None (added new principles); Development Workflow updated (removed strict TDD)
Added sections: Clean Code & Maintainability; Modular Architecture; Testing & Coverage Discipline
Removed sections: None
Templates requiring updates: ✅ .specify/templates/plan-template.md; ✅ .specify/templates/tasks-template.md; ✅ README.md (tests guidance optional); ⚠ pyproject.toml (add pytest-cov)
Follow-up TODOs:
- TODO(pytest-cov): Add pytest-cov to dev extras and wire coverage gate in CI
- TODO(ci-coverage-threshold): Enforce coverage ≥ 85% overall and ≥ 80% per-module
-->
# ZTE MC888 Ultra MQTT Daemon Constitution

## Core Principles

### Clean Code & Maintainability
**Non-Negotiables**
- Code MUST pass `ruff` lint and format checks with zero errors and warnings.
- Modules and public functions MUST include docstrings that explain purpose and side effects.
- Functions and classes MUST follow single-responsibility; avoid unnecessary complexity and dead code.
- Cyclic imports and tight coupling are prohibited; prefer clear, stable interfaces.
**Rationale**: Maintainable code lowers defect rates, accelerates feature delivery, and reduces operational risk.

### Modular Architecture
**Non-Negotiables**
- Separate concerns into modules/packages: `telemetry` (ZTE REST), `mqtt` (broker I/O), `pipeline` (poll→publish), `cli` (operations), `config` (loading/validation).
- Cross-module access MUST go through well-defined interfaces or protocols; avoid reaching into internals.
- Dependency direction MUST favor inversion where useful so implementation details can be swapped under tests.
- Public interfaces are considered contracts and MUST be versioned or documented when behavior changes.
**Rationale**: Modularity enables parallel work, easier testing, and safer refactors.

### End-to-End Modem Telemetry
**Non-Negotiables**
- The daemon MUST enumerate and fetch every publicly exposed attribute from the ZTE MC888 Ultra REST interface, capturing data value, units, and freshness metadata.
- Any unsupported attribute MUST be logged in a telemetry backlog and documented with its API path, expected type, and integration status.
- Polling workflows MUST fail gracefully with bounded retries and deliver the last known good data to prevent blind spots for downstream consumers.
**Rationale**: Smart home systems require a complete, dependable mirror of the modem state; gaps undermine automation and alerting.

### Local-Only Secure Communications
**Non-Negotiables**
- HTTP interactions with the modem MUST target private network addresses only (default `http://192.168.0.1`) and refuse reconfiguration to public endpoints without a recorded risk assessment.
- MQTT publishing MUST default to local broker credentials, with authentication and TLS options documented and enabled whenever the broker supports them.
**Rationale**: Constraining traffic to the local network prevents accidental data exposure and keeps the deployment aligned with the homeowner's security posture.

### Deterministic MQTT Publishing
**Non-Negotiables**
- Topic naming, payload schemas, and measurement units MUST be versioned, documented, and treated as contracts; breaking changes require a published migration note before release.
- The publish loop MUST work only with fresh data.
**Rationale**: Deterministic messaging keeps downstream automations correct and simplifies troubleshooting.

### Markdown Evidence Trail
**Non-Negotiables**
- Markdown documentation MUST cover the modem attribute catalog, MQTT topic map, CLI usage, configuration recipes, and deployment guidance.
- Any change to telemetry acquisition, schemas, or CLI behavior MUST update the relevant Markdown files within the same change set.
**Rationale**: Persistent, accurate documentation enables safe operation and handover without institutional memory loss.

### Operable CLI-First Service
**Non-Negotiables**
- Provide a Linux-ready executable and CLI that expose configuration flags for modem endpoint, polling cadence, MQTT connection details, and runtime modes (daemon, dry-run, diagnostics).
- The CLI MUST surface status commands to report modem connectivity, last publish timestamp, and broker handshake health.
- Exit codes and logging MUST distinguish configuration errors, connectivity faults, and runtime failures so that automation can react deterministically.
**Rationale**: A robust operational surface keeps the service manageable in unattended home server environments.

### Testing & Coverage Discipline
**Non-Negotiables**
- Tests MUST be part of every change; TDD is optional.
- Continuous integration on Linux MUST run `uv run pytest` for all changes and block merges on failures.
- Overall test coverage MUST be ≥ 85% with no critical modules below 80%; report coverage in CI.
- Integration tests MUST cover modem polling, MQTT publish/subscribe round-trips, and CLI diagnostics where feasible.
**Rationale**: High coverage and continuous testing catch regressions early without imposing a rigid workflow.

## Operational Constraints & Interfaces
- Modem integration uses the ZTE MC888 Ultra HTTP REST interface; requests leverage authenticated local sessions and MUST avoid disrupting the modem's native UI.
- MQTT communication targets a broker reachable on the local network; topic namespaces follow the documented schema version and include per-attribute subtopics.
- Configuration files and CLI flags MUST default to the canonical topology: modem at `192.168.0.1`, daemon on a Linux host, and broker on a distinct local address.
- Network transports MUST avoid cloud dependencies; any optional remote telemetry exports require an explicit opt-in feature proposal and governance review.

## Development Workflow & Quality Gates
- Prefer tests early; TDD is NOT required. Every change MUST include tests that exercise new behavior.
- CI MUST run on Linux and include: `uv run pytest`, coverage collection, and `ruff` lint/format checks.
- Coverage gates MUST enforce ≥ 85% overall and ≥ 80% per critical module; exceptions require documented rationale and an owner/date.
- Every pull request MUST attach evidence of documentation updates, sample MQTT messages, and connectivity test results against a local environment (real modem or emulator).
- Automated checks MUST validate schema versions, lint documentation for missing attribute entries, and ensure CLI help output matches documented options.
- Release candidates MUST pass integration tests covering modem polling, MQTT publish/subscribe round-trips, and CLI diagnostics commands on a Linux target.

## Governance
- This constitution defines mandatory practices for the ZTE MC888 Ultra MQTT Daemon; conflicting processes are superseded unless amended here.
- Amendments require consensus from project maintainers, a documented rationale, updated compliance checks, and simultaneous version/tag updates referencing the change.
- Versioning follows semantic versioning: MAJOR for breaking governance changes, MINOR for new principles or material expansions, PATCH for clarifications.
- Compliance reviews occur before every tagged release and quarterly thereafter; unresolved findings block release until rectified or explicitly deferred with owner and due date recorded.

**Version**: 1.1.0 | **Ratified**: 2025-10-06 | **Last Amended**: 2025-10-10

