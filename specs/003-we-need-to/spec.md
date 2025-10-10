# Feature Specification: MQTT-Driven ZTE Daemon (`zte run`)

**Feature Branch**: `003-we-need-to`  
**Created**: 2025-10-10  
**Status**: Draft  
**Input**: User description: "we need to implement the mqtt client with proper settings. update the partial implementation in src/cli/commands/run.py which will be the single entry point to this feature. it should work like a daemon running in background with optional --foreground flag. mqtt is configured and waits for request from mqtt broker, upon receiving topic, daemon uses src/services/zte_client.py to query requested information and publishes back. example: 1. mqtt broker publishes topic `/zte/provider/get` 2. daemon receives this topic and queries zte router using the client for this specific metric `provider`, same approach as in src/cli/commands/read.py should be used 3. when received information from router, daemon publishes information to channel `/zte/provider/set` in esence, `zte run` is using `zte read` implementation for requesting information from router mqtt options should be prefixed with `mqtt-` for example: --mqtt-host=192.168.0.242 --mqtt-port=1883 --mqtt-username=taphome --mqtt-password=pass --mqtt-topic=GeniaAir-split/%circuit/%name informations should be published to the topic in plain json format. --mqtt-topic is the root topic, `zte` is default --mqtt-port defaults to 1883"

## Clarifications
### Session 2025-10-10
- Q: What happens on `<root>/lte/get` aggregate requests? → A: Publish a JSON object with all metrics as defined in `docs/metrics.md` to `<root>/lte/set`.
- Q: Preferred JSON response shape for results? → A: Single metric: value only; Aggregate: object mapping all metrics.
- Q: How to handle single-metric failures (unknown metric/router error)? → A: Log error and publish nothing.
- Q: How to handle partial failures during `lte/get` aggregate? → A: Publish only successful metrics (omit failed); log failures.
- Q: MQTT QoS and retain flags? → A: QoS 0, retain false.
- Q: MQTT reconnect strategy? → A: Fixed retry every 5s forever.

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

## User Scenarios & Testing *(mandatory)*

### Primary User Story
As a home/office network operator, I want a long‑running `zte` daemon that listens for MQTT requests on a configurable root topic and, on demand, fetches the requested metric from the ZTE MC888 router and publishes the result back to a corresponding topic, so that my automations can query router status without direct router access.

### Acceptance Scenarios
1. **Given** the daemon is running with default settings, **When** the broker publishes to `/zte/provider/get` with any payload, **Then** the daemon queries the router for the `provider` metric and publishes the response as a value-only JSON to `/zte/provider/set` (no envelope).
2. **Given** the daemon is started with `--mqtt-topic=my/root`, **When** a message arrives at `/my/root/signal/get`, **Then** the daemon fetches the `signal` metric using the same identifiers supported by `zte read` and publishes JSON to `/my/root/signal/set`.
3. **Given** the daemon is started without `--foreground`, **When** the command returns control to the shell, **Then** the process continues running in the background as a daemon and continues serving MQTT requests.
4. **Given** the daemon is provided `--mqtt-host`, `--mqtt-port`, `--mqtt-username`, and `--mqtt-password`, **When** the MQTT broker requires authentication, **Then** the daemon connects successfully and starts subscribing to request topics.
5. **Given** the daemon is running, **When** the broker publishes to `/zte/lte/get`, **Then** the daemon publishes a JSON object containing all defined metrics to `/zte/lte/set`.
6. **Given** an unknown metric topic (e.g., `/zte/unknown/get`) or a router failure, **When** the daemon processes the request, **Then** it logs the error and publishes nothing to the corresponding `.../set` topic.
7. **Given** some metrics fail during an aggregate `/zte/lte/get`, **When** the daemon builds the response, **Then** it publishes only the successful metrics to `/zte/lte/set` and logs which metrics failed.

### Edge Cases
- Unknown metric requested (topic `/zte/unknown/get`): daemon MUST not crash; it MUST log an error and publish nothing.
- Router unreachable or returns error: daemon MUST log the error and publish nothing for that request; it SHOULD handle timeouts/retries gracefully [NEEDS CLARIFICATION: retry/backoff policy].
 - MQTT disconnects: daemon MUST attempt reconnect every 5s indefinitely without manual intervention.
- Large burst of requests: daemon SHOULD process sequentially or concurrently within safe limits [NEEDS CLARIFICATION: concurrency and rate limits].
- Message payload content: requests don’t need payloads, but if present they MUST be ignored safely unless future extensions define use [NEEDS CLARIFICATION].
- Topic normalization: leading/trailing slashes or mixed case in metric names [NEEDS CLARIFICATION: topic case sensitivity and normalization].
- Aggregate partial failure: daemon MUST publish only successful metrics; failed metrics are omitted and logged.

## Requirements *(mandatory)*

### Functional Requirements
- **FR-001**: Provide a `zte run` command that starts a long‑running router service which listens for MQTT request topics and publishes responses.
- **FR-002**: Support `--foreground` flag; without it, the service runs as a background daemon after initial startup confirmation.
- **FR-003**: Accept MQTT options with `mqtt-` prefix: `--mqtt-host`, `--mqtt-port` (default `1883`), `--mqtt-username`, `--mqtt-password`, `--mqtt-topic` (root topic, default `zte`).
- **FR-004**: Subscribe to request topics under the configured root as `<root>/<metric>/get`; metrics MUST align with the identifiers accepted by `zte read`.
- **FR-005**: Upon receiving a request, fetch the corresponding router metric using the same logic and identifiers as the `zte read` command.
- **FR-006**: Publish results as plain JSON to `<root>/<metric>/set`.
- **FR-007**: Logging MUST indicate connection state, subscriptions, request handling, publish outcomes, and errors at appropriate levels for operations visibility.
- **FR-008**: The service MUST validate and sanitize metric identifiers derived from topic segments to avoid unsafe inputs.
- **FR-009**: MQTT authentication (username/password) MUST be supported when provided; lack of credentials MUST still allow connecting to open brokers.
- **FR-010**: On graceful shutdown (e.g., SIGINT/SIGTERM), the service SHOULD disconnect from MQTT and stop cleanly.
- **FR-011**: The daemon MUST not require users or automations to know router credentials beyond what is already needed by existing `zte` commands [NEEDS CLARIFICATION: reuse of global/router options and configuration source].
- **FR-012**: JSON response schema: single metric responses MUST be value-only JSON (e.g., string/number/boolean); aggregate `lte` responses MUST be a JSON object mapping metric→value; no envelope by default.
- **FR-012a**: For the aggregate request `<root>/lte/get`, the daemon MUST publish a JSON object including all metrics defined in `docs/metrics.md` to `<root>/lte/set`.
- **FR-016**: On single-metric failures (unknown metric, router error), the daemon MUST log an error and MUST NOT publish any message to the corresponding `.../set` topic.
- **FR-017**: For aggregate `lte/get`, if some metrics fail, the daemon MUST publish only successful metrics (omit failed) and MUST log the failed metric names.
- **FR-018**: MQTT publishes MUST use QoS 0 and retain=false.
- **FR-019**: On MQTT disconnect, the daemon MUST retry reconnect every 5 seconds indefinitely.

*Example of marking unclear requirements:*
- **FR-013**: QoS and retain flags for MQTT publishes [NEEDS CLARIFICATION: required QoS level and whether messages should be retained].
- **FR-014**: TLS support for MQTT connections [NEEDS CLARIFICATION: whether TLS and certificates are needed].
- **FR-015**: Rate limiting and concurrency [NEEDS CLARIFICATION: limits and execution model].

### Key Entities *(include if feature involves data)*
- **Metric**: Human‑readable identifier of router information (e.g., `provider`, `signal`). Must match `zte read` supported identifiers.
- **MQTT Topic Root**: Base topic under which requests and responses flow (default `zte`).
- **Request Topic**: `<root>/<metric>/get` indicating a request to fetch `<metric>`.
- **Response Topic**: `<root>/<metric>/set` carrying the JSON response to the request.
- **Aggregate Request `lte`**: A special request topic `<root>/lte/get` instructing the daemon to respond with all metrics as a single JSON object at `<root>/lte/set`.

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
