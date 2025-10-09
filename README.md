# ZTE MC888 Ultra Daemon

Developer-focused CLI for the ZTE MC888 Ultra. It ships a Click-based `zte` CLI with `run`, `read`, and `discover` commands, structured logging, in-memory snapshots with on-disk fixtures, and a mock MQTT broker for offline development.

## Requirements
- Python 3.12 (recommended to manage with `uv`)
- `uv` for running tools without a local venv (optional but recommended)

Bootstrap with uv:

```bash
uv python install 3.12
uv sync
```

## CLI Usage
See `docs/cli.md` for full command help. Quick examples:

```bash
# Show help
uv run zte --help

# Run mocked daemon once and record an MQTT payload
uv run zte run \
  --router-host 192.168.0.1 \
  --router-password secret \
  --foreground \
  --log warn \
  --log-file ./logs/zte.log \
  --mqtt-host 192.168.0.50:8080 \
  --mqtt-topic zte-modem

# Read a metric (live via REST if host/password provided, otherwise from the mock fixture)
uv run zte read provider
uv run zte read lte.rsrp1

# Discover modem endpoints and optionally write a Markdown example
uv run zte discover \
  --router-host http://192.168.0.1 \
  --router-password secret \
  --path "goform/goform_get_cmd_process?isTest=false&cmd=lan_station_list" \
  --target-file docs/discover/lan_station_list.md
```

Notes:
- `run` reads the latest modem snapshot from `tests/fixtures/modem/latest.json` and writes a mock publish into `logs/mqtt-mock.jsonl`.
- `read` supports identifiers like `lte.rsrp1`, `nr5g.pci`, `wan_ip`, `provider`, and a `neighbors[...]` selector when using live REST.
- `discover` logs in to the modem, performs the request, and when `--target-file` is set it also writes a JSON snapshot alongside the Markdown example.

## Tests
Run tests without installing pytest into the environment by using uv to resolve it on-demand:

```bash
uv run --with pytest pytest
```

Alternatively, use dev extras:

```bash
# one-off (resolve extras just for this run)
uv run --with .[dev] pytest

# or install dev extras, then run normally
uv sync --extra dev
uv run pytest
```

## Linting and Formatting
Ruff handles linting, import sorting, and formatting. The project targets Python 3.12 and uses a max line length of 120.

Without installing anything locally:

```bash
uvx ruff check .
uvx ruff check . --fix
uvx ruff format
```

Using uv within the project environment:

```bash
uv run --with ruff ruff check .
uv run --with ruff ruff check . --fix
uv run --with ruff ruff format
```

## Pre-commit
Pre-commit is configured in `.pre-commit-config.yaml` and runs Ruff on commit.

```bash
uvx pre-commit install          # install git hook
uvx pre-commit run -a           # run hooks on all files
```

## Project Structure
- `src/` CLI and services implementation
- `tests/` unit, integration, and contract tests
- `docs/discover/` captured examples from the `discover` command
