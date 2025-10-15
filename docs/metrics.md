# ZTE MC888 Ultra Metrics Catalog

This catalog defines stable metric identifiers used by the `zte read` command,
and how they map to MQTT request/response topics when running `zte run`.

Identifiers follow a dot-path convention with optional array indices:

- Format: `<namespace>.<field>` with optional `[index]` for lists.
- Examples: `lte.rsrp1`, `nr5g.pci`, `wan_ip`, `temp.a`, `neighbors`, `neighbors[0].id`.
- Identifiers are case-insensitive.


## MQTT Topics and Grouping

All MQTT requests and responses are nested under a single logical `zte` group.

- Root prefix: optional. Provided via `--mqtt-topic` on `zte run`.
- Effective prefix used by the daemon: `<root>/zte` (if no `--mqtt-topic`, just `zte`).
- Request pattern: `<effective-prefix>/<metric>/get` for single metrics.
- Aggregate requests:
  - `<effective-prefix>/lte/get` returns an object with LTE-only metrics.
  - `<effective-prefix>/get` (no metric segment) returns a nested object with all data grouped by logical area (`lte`, `nr5g`, `temp`, and top-level info like `provider`, `connection`, etc.).

Examples (no custom root):

- Request topic `zte/lte/rsrp1/get` → Response topic `zte/lte/rsrp1` with a number.
- Request topic `zte/lte/get` → Response topic `zte/lte` with an object of LTE metrics.
- Request topic `zte/get` → Response topic `zte` with a nested object of all metrics.


## LTE Metrics
- `lte.rsrp1` – LTE primary cell RSRP (dBm)
- `lte.sinr1` – LTE primary cell SINR (dB)
- `lte.rsrp2` – Secondary cell RSRP (dBm)
- `lte.sinr2` – Secondary cell SINR (dB)
- `lte.rsrp3` – Third cell RSRP (dBm)
- `lte.sinr3` – Third cell SINR (dB)
- `lte.rsrp4` – Fourth cell RSRP (dBm)
- `lte.sinr4` – Fourth cell SINR (dB)
- `lte.rsrq` – LTE signal quality (dB)
- `lte.rssi` – LTE received signal strength indicator (dBm)
- `lte.earfcn` – LTE EARFCN/frequency identifier (best-effort from pcell)
- `lte.pci` – LTE Physical Cell ID
- `lte.bw` – LTE primary cell bandwidth description (e.g., `10MHz`)

## NR5G Metrics
- `nr5g.rsrp1` – NR primary receive chain RSRP (dBm)
- `nr5g.rsrp2` – NR secondary receive chain RSRP (dBm)
- `nr5g.sinr` – NR SINR (dB)
- `nr5g.arfcn` – NR ARFCN/channel (active)
- `nr5g.pci` – NR Physical Cell ID

## Provider
- `provider` – Network operator full name reported by the modem UI.

## Cell
- `cell` – Serving cell identifier for the LTE anchor.

## Neighbor Cells
- `neighbors[].id` – Neighbor cell identifier.
- `neighbors[].rsrp` – Neighbor RSRP (dBm).
- `neighbors[].rsrq` – Neighbor RSRQ (dB).

Neighbors map to the modem field `ngbr_cell_info` and are exposed as objects
parsed from entries shaped like `freq,pci,rsrq,rsrp,rssi`.

- `zte read "neighbors"` returns a JSON array of neighbor objects.
- `zte read "neighbors[0]"` returns a JSON object for the first neighbor.
- `zte read "neighbors[0].id"` returns a scalar field from the first neighbor.

## Connection State
- `connection` – Aggregated connection mode (e.g., `ENDC`).

## Bands
- `bands` – Combined LTE/NR band summary such as `B20(10MHz) + n28(10MHz)`.

## WAN IP
- `wan_ip` – Public WAN IP address assigned to the modem.

## Temperatures
- `temp.a` – Ambient temperature sensor (°C).
- `temp.m` – Modem/baseband temperature sensor (°C).
- `temp.p` – Power amplifier temperature sensor (°C).

### Notes on Stability
- The identifier surface aims to be stable across firmware versions.
- If a value is missing in the modem response, the CLI reports a helpful error.
