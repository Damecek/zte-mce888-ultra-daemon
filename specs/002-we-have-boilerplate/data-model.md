# Data Model: ZTE Modem REST Metrics & Discover CLI

## Entities

### Modem Session
- authenticated: bool
- cookies: map<string,string>
- token: string | null
- expires_at: datetime | null
- host: string

Constraints:
- Host must be a private IP/hostname.
- Session must refresh or re-login on expiry.

### Endpoint Request
- path: string (relative to modem root)
- method: enum[GET, POST]
- payload: object | string | null
- headers: map<string,string>
- expects: enum[json, text]

Constraints:
- Default method GET when payload is null; POST when payload present unless overridden.

### Metric Snapshot
- timestamp: datetime
- host: string
- lte: object (B20 metrics) → { rsrp1, sinr1, rsrp2, sinr2, rsrp3, sinr3, rsrp4, sinr4, rsrq, rssi, earfcn, pci, bw }
- nr5g: object (n28 metrics) → { rsrp1, rsrp2, sinr, arfcn, pci, bw }
- provider: string
- cell: string
- neighbors: array<object> → { id, rsrp, rsrq }
- connection: string (e.g., ENDC)
- bands: string (e.g., "B20(10MHz) + n28(10MHz)")
- wan_ip: string
- temp: object → { a, m, p }

Constraints:
- Units tracked in docs; values are raw as reported.

### Discover Example File
- location: string (path under docs/discover)
- request: { path, method, payload }
- response: string | object

Constraints:
- Stored as Markdown with fenced code blocks for request and response.

