# ZTE MC888 Ultra Daemon

This repository contains a developer-oriented CLI for the ZTE MC888 Ultra daemon. It ships a Click-based `zte` CLI with
`run`, `read`, and `discover` commands, structured logging, modem telemetry fixtures, and a mock MQTT broker so developers can
practice the workflow without live hardware.

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

The `run` command reads the latest modem snapshot from `tests/fixtures/modem/latest.json` and stores
 a mocked MQTT publish in `logs/mqtt-mock.jsonl`. Optionally, you can exercise a minimal REST client login using `--rest-test`.

To inspect individual telemetry metrics:

```bash
uv run zte read RSRP
uv run zte read Provider
```

### Discover modem endpoints

The new `discover` command authenticates against the modem's REST API, executes an arbitrary endpoint, and optionally writes
Markdown examples under `docs/discover/` (see [`docs/cli.md`](docs/cli.md) for detailed usage).

```bash
uv run zte discover \
  --host 192.168.0.1 \
  --password secret \
  --path "goform/goform_get_cmd_process?isTest=false&cmd=lan_station_list" \
  --target-file docs/discover/lan_station_list.md
```

Captured examples appear alongside the generated JSON snapshots to support contract tests and fixture authoring.

## Capturing Real Modem Fixtures
1. Authenticate against the local modem web UI.
2. Execute `curl -s http://192.168.0.1/cgi-bin/modem/status` and save the JSON to
   `tests/fixtures/modem/samples/YYYYMMDD-status.json`.
3. Replace `tests/fixtures/modem/latest.json` with the new capture.
4. Re-run the CLI or tests to replay the latest telemetry.

## Tests
Recommended (installs pytest transiently and works without a dev venv):

```bash
uv run --with pytest pytest
```

If you prefer using the project dev extras, either:

```bash
# one-off: bring in dev extras for this run
uv run --with .[dev] pytest

# or install dev extras into the environment, then run normally
uv sync --extra dev
uv run pytest
```

Unit tests cover CLI help contracts, command behavior, modem fixture handling, modem discovery flows, and MQTT payload schemas.
Integration tests run the hello-world and discover flows end-to-end using the mocks.

## Linting & Formatting
Use Ruff for lint checks, import sorting, auto-fixes, a formátování kódu.

Quick usage (no local install needed):

```bash
uvx ruff check .
uvx ruff check . --fix
uvx ruff format
```

Alternatively, pokud chceš Ruff v prostředí projektu:

```bash
uv run --with ruff ruff check .
uv run --with ruff ruff check . --fix
uv run --with ruff ruff format
```

### Pre-commit hook
Konfigurace je v `.pre-commit-config.yaml`. Pro aktivaci hooků:

```bash
uvx pre-commit install
# Spustit hooky na celé repo
uvx pre-commit run -a
```
