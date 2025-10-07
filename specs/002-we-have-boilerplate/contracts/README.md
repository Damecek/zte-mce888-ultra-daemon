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

1. **Challenge request**
   - `GET /goform/goform_get_cmd_process`
   - Query: `cmd=wa_inner_version,cr_version,RD,LD` and `multi_data=1`
   - Response JSON includes salts `wa_inner_version`, `cr_version`, `RD`, and `LD`
2. **Derived fields**
   - `AD = SHA256(SHA256(wa_inner_version + cr_version) + RD)`
   - `password = SHA256(SHA256(user_password) + LD)`
3. **Login submission**
   - `POST /goform/goform_set_cmd_process`
   - Form data: `isTest=false`, `goformId=LOGIN`, `password=<hashed>`, `AD=<derived>`
   - Success payload: `{"result": "0"}` and `Set-Cookie: SessionID=<value>`
   - Failure payload: `{"result": "3"}` indicates wrong password; `{"result": "1"}` indicates throttling/try later

Sessions rely on the `SessionID` cookie. The client must retry the login flow if
subsequent requests receive HTTP 401/403.

### Example: LAN Station List
- Path: `goform/goform_get_cmd_process?isTest=false&cmd=lan_station_list`
- Method: GET
- Response: JSON (array/object per device entries) [capture via discover and store in docs/discover]
