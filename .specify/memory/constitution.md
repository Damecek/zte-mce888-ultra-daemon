<!--
Sync Impact Report
Version change: N/A → 1.0.0
Modified principles: [PRINCIPLE_1_NAME] → End-to-End Modem Telemetry; [PRINCIPLE_2_NAME] → Local-Only Secure Communications; [PRINCIPLE_3_NAME] → Deterministic MQTT Publishing; [PRINCIPLE_4_NAME] → Markdown Evidence Trail; [PRINCIPLE_5_NAME] → Operable CLI-First Service
Added sections: Operational Constraints & Interfaces; Development Workflow & Quality Gates
Removed sections: None
Templates requiring updates: ✅ .specify/templates/plan-template.md; ✅ .specify/templates/spec-template.md; ✅ .specify/templates/tasks-template.md
Follow-up TODOs: None
-->
# ZTE MC888 Ultra MQTT Daemon Constitution

## Core Principles

### End-to-End Modem Telemetry
**Non-Negotiables**
- The daemon MUST enumerate and fetch every publicly exposed attribute from the ZTE MC888 Ultra REST interface, capturing data value, units, and freshness metadata.
- Any unsupported attribute MUST be logged in a telemetry backlog and documented with its API path, expected type, and integration status.
- Polling workflows MUST fail gracefully with bounded retries and deliver the last known good data to prevent blind spots for downstream consumers.
**Rationale**: Smart home systems require a complete, dependable mirror of the modem state; gaps undermine automation and alerting.

### Local-Only Secure Communications
**Non-Negotiables**
- HTTP interactions with the modem MUST target private network addresses only (default `http://192.169.0.1`) and refuse reconfiguration to public endpoints without a recorded risk assessment.
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

## Operational Constraints & Interfaces
- Modem integration uses the ZTE MC888 Ultra HTTP REST interface; requests leverage authenticated local sessions and MUST avoid disrupting the modem's native UI.
- MQTT communication targets a broker reachable on the local network; topic namespaces follow the documented schema version and include per-attribute subtopics.
- Configuration files and CLI flags MUST default to the canonical topology: modem at `192.169.0.1`, daemon on a Linux host, and broker on a distinct local address.
- Network transports MUST avoid cloud dependencies; any optional remote telemetry exports require an explicit opt-in feature proposal and governance review.

## Development Workflow & Quality Gates
- Follow test-driven development for schema and CLI changes: write contract tests for REST responses and MQTT payloads before implementation.
- Every pull request MUST attach evidence of documentation updates, sample MQTT messages, and connectivity test results against a local environment (real modem or emulator).
- Automated checks MUST validate schema versions, lint documentation for missing attribute entries, and ensure CLI help output matches documented options.
- Release candidates MUST pass integration tests covering modem polling, MQTT publish/subscribe round-trips, and CLI diagnostics commands on a Linux target.

## Governance
- This constitution defines mandatory practices for the ZTE MC888 Ultra MQTT Daemon; conflicting processes are superseded unless amended here.
- Amendments require consensus from project maintainers, a documented rationale, updated compliance checks, and simultaneous version/tag updates referencing the change.
- Versioning follows semantic versioning: MAJOR for breaking governance changes, MINOR for new principles or material expansions, PATCH for clarifications.
- Compliance reviews occur before every tagged release and quarterly thereafter; unresolved findings block release until rectified or explicitly deferred with owner and due date recorded.

**Version**: 1.0.0 | **Ratified**: 2025-10-06 | **Last Amended**: 2025-10-06
