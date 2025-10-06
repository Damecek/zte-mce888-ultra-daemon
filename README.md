# ZTE MC888 Ultra Daemon (Hello World)

This repository contains a mocked hello-world experience for the ZTE MC888 Ultra daemon. It ships a Click-based `zte` CLI with
`run` and `read` commands, structured logging, modem telemetry fixtures, and a mock MQTT broker so developers can practice the
workflow without live hardware.

## Prerequisites
- Python 3.12 (managed via [uv](https://github.com/astral-sh/uv) if desired)
- Recommended dependencies installed with `uv` or `pip`

```bash
uv python install 3.12
uv sync
```

If you prefer pip, install dependencies from `pyproject.toml`.

## Running the CLI
Use the console script provided by `pyproject.toml`:

```bash
uv run zte run --device-pass secret --foreground --log warn --log-file ./logs/zte.log \
  --mqtt-host 192.168.0.50:8080 --mqtt-topic zte-modem
```

The `run` command reads the latest modem snapshot from `tests/fixtures/modem/latest.json`, prints a friendly greeting, and stores
a mocked MQTT publish in `logs/mqtt-mock.jsonl`.

To inspect individual telemetry metrics:

```bash
uv run zte read RSRP
uv run zte read Provider
```

## Capturing Real Modem Fixtures
1. Authenticate against the local modem web UI.
2. Execute `curl -s http://192.168.0.1/cgi-bin/modem/status` and save the JSON to
   `tests/fixtures/modem/samples/YYYYMMDD-status.json`.
3. Replace `tests/fixtures/modem/latest.json` with the new capture.
4. Re-run the CLI or tests to replay the latest telemetry.

## Tests
Execute the full suite via:

```bash
uv run pytest
```

Unit tests cover CLI help contracts, command behavior, modem fixture handling, and MQTT payload schemas. Integration tests run
the hello-world flow end-to-end using the mocks.
