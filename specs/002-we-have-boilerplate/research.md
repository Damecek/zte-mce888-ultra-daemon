# Research: ZTE Modem REST Metrics & Discover CLI

Date: 2025-10-06

## Unknowns and Resolutions

1) Authentication flow specifics (endpoint, method, tokens)
- Resolution: Use `js_implementation.js` as source of truth. Extract login URL, parameters (including hashing/salting), cookies/token names, CSRF use, and retry/expiry behavior.
- Human steps (if needed):
  - Open modem UI at `http://192.168.0.1/` and login normally.
  - Use browser DevTools → Network to capture the login request and subsequent authenticated API calls.
  - Record: request method, URL path, headers, form data/body, response codes, set-cookie headers, and any CSRF/token fields.
  - Share captured details verbatim for contract finalization.

2) Initial metrics endpoint coverage
- Resolution: Implement all metrics rendered by the JS snippet inserted into modem DOM, including LTE/5G radio metrics, provider/cell, neighbor cells, connection/bands, WAN IP, and temperatures (A/M/P).
- Source: `js_implementation.js` functions that fetch and parse metrics.

3) HTTP client library choice
- Resolution: Chosen `httpx` for its unified sync/async API and excellent test utilities (`httpx.MockTransport`) while remaining fully compatible with Python 3.12 CLI workflows.
- Decision target: Phase 1 before coding.

4) Rate limiting / throttling behavior
- Resolution: Unknown. Implement backoff with single retry and surface clear error. Revisit after initial integration.

5) Discover examples repository path
- Resolution: Use `docs/discover` for Markdown inputs/outputs. CLI supports `--target-file` to write results there and prints the final path.

## Decisions

- Method defaults: GET when no payload; POST when payload; `--method` overrides.
- Logging: No redaction; user responsibility in local environment.
- Examples: Store under `docs/discover` with filename convention `<timestamp>-<sanitized-endpoint>.md` (proposed).

## Alternatives Considered

- Store examples under `specs/002.../discover-examples`: Rejected to keep shared examples in a stable docs location across features.
- Force POST for all discover calls: Rejected; defaults should reflect typical REST usage and minimize surprises.

