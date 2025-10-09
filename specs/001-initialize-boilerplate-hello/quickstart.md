# Quickstart - Initialize Boilerplate Hello World

## Prerequisites
- Linux or macOS terminal with `uv` installed (`pip install uv` or follow uv docs).
- Python 3.12 available (uv downloads automatically via `python = "3.12"`).
- Local network access to ZTE MC888 Ultra modem (for optional real capture).

## Environment Setup
```bash
uv init . --package
uv python install 3.12
uv add click gmqtt pytest pytest-asyncio anyio rich
```

## Running the Hello-World Daemon
```bash
uv run zte run   --device-host 192.168.0.1   --device-pass password   --log warn   --foreground   --log-file ./logs/zte.log   --mqtt-host 192.168.0.50:8080   --mqtt-topic zte-modem   --mqtt-user taphome   --mqtt-password pass
```
- The mock modem client loads fixtures from `tests/fixtures/modem/latest.json`.
- MQTT publishing is mocked; messages are recorded to `logs/mqtt-mock.jsonl` for inspection.
- Standard logging writes to stdout and `./logs/zte.log`.

## Reading Mocked Metrics Interactively
```bash
uv run zte read RSRP
uv run zte read Provider
```
Each command prints a single value from the current `ModemTelemetrySnapshot` and logs the access.

## Capturing Real Modem Responses
1. Run `curl -s http://192.168.0.1/cgi-bin/modem/status` while authenticated to the modem UI.
2. Save output to `tests/fixtures/modem/YYYYMMDD-status.json`.
3. Update `tests/fixtures/modem/latest.json` to point to the new capture (symbolic link or copy).
4. Re-run `uv run zte run` to replay with real data in mocked environment.

## Running Tests
```bash
uv run pytest
```
- Contract tests validate CLI help, modem fixture schema, and MQTT placeholder payloads.
- Integration tests execute the hello-world flow end-to-end with mocks.
- Use `uv run pytest tests/unit -k cli` for focused development.

## Observability
- Logging level configured with `--log` flag; defaults to `WARN` if omitted.
- Mock MQTT publishes recorded with timestamp, topic, payload, and publish outcome for deterministic inspection.

## Cleanup
- Remove generated logs with `rm -rf logs`.
- Clear fixture captures if they contain sensitive provider information before committing.
