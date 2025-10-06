# Phase 0 Research - Initialize Boilerplate Hello World

## uv-managed Python stability channel
- **Decision**: Pin the project to `python = "3.12"` in `pyproject.toml` while allowing uv to track the stable channel for patch updates.
- **Rationale**: Python 3.12 is the current uv stable baseline, offers performance improvements for async IO used by gmqtt, and keeps the hello-world aligned with downstream production expectations.
- **Alternatives considered**: Relying on uv's floating `python = "stable"` tag (rejected due to non-deterministic CI behaviour); downgrading to Python 3.11 (rejected because upcoming gmqtt features target 3.12+).

## Offline-friendly gmqtt patterns
- **Decision**: Implement a `MockGMQTTClient` wrapper that mirrors the gmqtt API surface, recording publish requests and simulating connection lifecycle without network sockets.
- **Rationale**: Keeps the code aligned with gmqtt usage while enabling dry-run hello-world demonstrations and deterministic tests that never require a live broker.
- **Alternatives considered**: Using the built-in `asyncio` mock transports (rejected because gmqtt expects its own client); swapping to `paho-mqtt` for mocks (rejected due to divergence from target dependency).

## Capturing modem REST responses for fixtures
- **Decision**: Document a workflow in quickstart.md where operators run `curl` commands against the local modem (`/cgi-bin/modem/status/*`) and store JSON dumps under `tests/fixtures/modem/` for replay.
- **Rationale**: Matches human-in-the-loop expectation, keeps sensitive data local, and creates reusable fixtures for contract tests without bundling proprietary payloads.
- **Alternatives considered**: Shipping synthetic sample payloads only (rejected because missing real-world field coverage); building an HTTP proxy capture tool (deferred until after hello-world milestone).
