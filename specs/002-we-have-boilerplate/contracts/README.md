# Contracts: ZTE Modem REST Metrics & Discover CLI

This folder defines request/response contracts used for mocking and tests.

## CLI Contract: `zte discover`

Inputs
- `--host`: Modem host/IP (required; no default)
- `--path`: Relative endpoint path (e.g., `goform/goform_get_cmd_process?isTest=false&cmd=lan_station_list`)
- `--payload`: Optional data; when provided default method becomes POST; encoded as JSON with `Content-Type: application/json` by default
- `--method`: Optional override (GET|POST)
- `--target-file`: Optional Markdown file path under `docs/discover` to write example

Behavior
- Default method GET if no payload; POST if payload present; `--method` overrides.
- Prints raw response to stdout and exits non-zero on error.
- When `--target-file` provided: writes a Markdown file containing request/response and prints the absolute path.

## HTTP Contracts

### Authentication (from js_implementation.js)
- **Challenge request**: `GET /goform/goform_get_cmd_process` with query params `cmd=wa_inner_version,cr_version,RD,LD` and `multi_data=1`. Response includes the challenge values `wa_inner_version`, `cr_version`, `RD`, and `LD`.
- **Hash selection**: For MC888/MC889 the script uses SHA256, otherwise it falls back to MD5. Python client mirrors this behavior.
- **Login request**: `POST /goform/goform_set_cmd_process` with form data `isTest=false`, `goformId=LOGIN`, `password=SHA256(SHA256(password) + LD)`, `AD=SHA256(SHA256(wa_inner_version + cr_version) + RD)`.
- **Session token**: Successful responses return `{"result":"0"}` and include a `Set-Cookie` header (e.g., `SESSIONID=<value>`). Subsequent API calls must send the cookie unchanged.

### Example: LAN Station List
- Path: `goform/goform_get_cmd_process?isTest=false&cmd=lan_station_list`
- Method: GET
- Response: JSON (array/object per device entries) [capture via discover and store in docs/discover]
