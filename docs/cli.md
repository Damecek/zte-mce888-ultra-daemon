# ZTE CLI Reference

## `zte discover`
Invoke a modem REST endpoint and optionally capture the response as Markdown and JSON fixtures.

### Options
- `--host` (default: `http://192.168.0.1`) – Modem base URL.
- `--password` (required) – Admin password used for login.
- `--path` (required) – Relative path for the modem endpoint.
- `--payload` – Optional payload string. When provided the command defaults to POST unless `--method` overrides.
- `--method` – Explicit HTTP method (`GET` or `POST`). Overrides the default behavior.
- `--target-file` – Markdown file path under `docs/discover/` where the example should be written. The absolute path is printed on success.

### Behavior
1. Authenticates using the modem's challenge/response flow.
2. Executes the request with automatic cookie/session handling and a single retry when the session expires.
3. Prints the response to stdout (pretty-printed JSON when applicable).
4. When `--target-file` is provided, writes a Markdown example and JSON snapshot alongside it.

### Examples
```bash
zte discover \
  --host 192.168.0.1 \
  --password secret \
  --path "goform/goform_get_cmd_process?isTest=false&cmd=lan_station_list" \
  --target-file docs/discover/lan_station_list.md
```

```bash
zte discover \
  --host 192.168.0.1 \
  --password secret \
  --path "goform/goform_set_cmd_process" \
  --payload '{"foo": "bar"}'
```
