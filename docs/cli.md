# ZTE CLI Reference

The `zte` command-line interface interacts with the MC888 Ultra modem using the
REST flow reverse-engineered from the web UI. All commands require Python 3.12
and the dependencies listed in `pyproject.toml` (install via `uv` or
`pip install -e .`). Invoke the CLI via `python -m zte_daemon.cli.main` or the
installed entry point `zte`.

## Global Usage

```bash
zte [OPTIONS] COMMAND [ARGS...]
```

Run `zte --help` to list the available subcommands and options. Each command
supports `--log` (log level) and, where applicable, `--log-file` to write
structured JSON logs using `zte_daemon.logging.config`.

## `zte discover`

Issue an authenticated REST request against the modem and print the raw
response. This command is ideal for exploring undocumented endpoints and
capturing fixtures for tests.

```bash
zte discover --host 192.168.0.1 --password <password> --path <relative-path> [OPTIONS]
```

### Options

- `--host`: **Required.** Modem hostname or IP (e.g., `192.168.0.1`).
- `--password`: **Required.** Modem admin password. No username is needed.
- `--path`: **Required.** Relative API path (for example,
  `goform/goform_get_cmd_process?cmd=lan_station_list`).
- `--payload`: Optional JSON payload string. When provided the request defaults
  to `POST` unless `--method` overrides it.
- `--method`: Optional explicit HTTP method (`GET` or `POST`). Overrides
  automatic defaults.
- `--target-file`: Optional Markdown output path (under `docs/discover/`). When
  supplied, the CLI writes both a Markdown transcript and a JSON payload next to
  the file using `zte_daemon.lib.markdown_io.write_discover_example` and
  `zte_daemon.lib.snapshots.write_snapshot`.
- `--expects`: Response type (`json` or `text`). Defaults to `json`.
- `--timeout`: Request timeout in seconds (default `10`).
- `--log` / `--log-file`: Control logging verbosity and optional log file.

### Example

```bash
zte discover \
  --host 192.168.0.1 \
  --password hunter2 \
  --path "goform/goform_get_cmd_process?isTest=false&cmd=lan_station_list" \
  --target-file docs/discover/lan_station_list.md
```

The command prints the modem response, writes a Markdown request/response pair,
logs the operation, and stores a JSON snapshot alongside the Markdown file for
fixture reuse.

## `zte read`

Fetch a full modem snapshot, then print a single metric (case-insensitive).

```bash
zte read <METRIC> --host 192.168.0.1 --password <password> [OPTIONS]
```

### Options

- `METRIC`: Metric key such as `RSRP1`, `provider`, `bands`, or
  `temp (A/M/P)`.
- `--host`: **Required.** Modem hostname or IP.
- `--password`: **Required.** Modem password.
- `--timeout`: Request timeout (seconds, default `10`).
- `--log` / `--log-file`: Logging controls identical to `discover`.

Unknown metrics trigger a helpful error listing the supported keys extracted
from the most recent snapshot.

### Example

```bash
zte read RSRP1 --host 192.168.0.1 --password hunter2
```

## `zte run`

Execute a one-shot daemon cycle: authenticate, capture a snapshot, print a few
high-value metrics, and publish the payload to the mocked MQTT broker.

```bash
zte run --device-pass <password> [OPTIONS]
```

### Options

- `--device-host`: Modem host/IP (default `192.168.0.1`).
- `--device-pass`: **Required.** Modem password.
- `--foreground`: Keep execution in the foreground (default); flag retained for
  compatibility with future long-running modes.
- `--timeout`: Request timeout (seconds, default `10`).
- `--mqtt-host`, `--mqtt-topic`, `--mqtt-user`, `--mqtt-password`: Metadata
  stored with the mock publish record.
- `--log` / `--log-file`: Structured logging controls.

The command prints the host, primary RSRP, provider, and a summary of the mock
MQTT publish location. The mock broker persists publishes to `logs/mqtt-mock.jsonl`
for offline inspection.

## Error Handling

All commands surface consistent error messages:

- Connectivity problems: `Unable to reach modem at <host>.`
- Authentication failures: `Authentication failed: verify modem credentials.`
- Invalid JSON payloads or unexpected responses raise descriptive Click
  exceptions and exit non-zero.

Session expiry is handled transparently—the REST client retries once after a
401/403 response before surfacing an error.

## Capturing Fixtures

Use `zte discover --target-file ...` to bootstrap fixtures. The Markdown output
documents the request and response, and the adjacent JSON file can be copied
into `tests/fixtures/` (or similar) for future mocking.
