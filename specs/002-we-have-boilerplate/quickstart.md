# Quickstart: ZTE Modem REST Metrics & Discover CLI

## Prerequisites
- Python 3.12 (uv-managed)
- Local network access to ZTE modem (provide host via `--host`)

## Discover Examples
- Ensure folder exists: `docs/discover`

## CLI Examples

Discover LAN stations (GET by default):
```
zte discover --host 192.168.0.1 \
  --path "goform/goform_get_cmd_process?isTest=false&cmd=lan_station_list" \
  --target-file docs/discover/lan_station_list.md
```

POST with payload (method defaults to POST when payload present):
```
zte discover --host 192.168.0.1 \
  --path "goform/some_post_endpoint" \
  --payload '{"foo":"bar"}' \
  --target-file docs/discover/some_post_endpoint.md
```

Note: `--payload` is encoded as JSON by default and sent with `Content-Type: application/json`.

Override method explicitly:
```
zte discover --method GET --payload '{}' --path "goform/special" --target-file docs/discover/special.md
```

## Next Steps
- Use captured examples in `docs/discover` to build mocks and contract tests.
- Extract auth flow details from `js_implementation.js` and record in contracts.
