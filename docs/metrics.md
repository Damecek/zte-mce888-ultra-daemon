# ZTE MC888 Ultra Telemetry Metrics

This document tracks the REST-derived metrics captured by the `zte` CLI. Every metric listed below must be present in modem captur
es and validated by automated tests.

## Radio Metrics (LTE)
- `rsrp1`–`rsrp4`: Primary and secondary Reference Signal Received Power levels (dBm)
- `sinr1`–`sinr4`: Signal-to-Interference-plus-Noise Ratio per carrier (dB)
- `rsrq`: Reference Signal Received Quality (dB)
- `rssi`: Received Signal Strength Indicator (dBm)
- `bands`: Active LTE band aggregation summary reported by the modem
- `earfcn`: Primary EARFCN channel identifier
- `pci`: Physical cell identifier for the LTE serving cell

## Radio Metrics (5G NR)
- `nr5g_rsrp`: Primary NR signal strength
- `nr5g_sinr`: NR signal-to-noise ratio
- `nr5g`: Metadata section covering ARFCN, PCI, and bandwidth details returned by the modem API

## Provider & Network Identification
- `provider`: Display name reported by the network_provider_fullname field
- `cell`: Serving cell identifier
- `connection`: End-to-end connection mode (e.g., LTE, ENDC)
- `wan_ip`: WAN IPv4/IPv6 address assigned to the modem

## Temperature Sensors
- `temp (A/M/P)`: Tuple representing antenna, modem, and power amplifier temperature channels respectively

## Neighbor Cells
The modem returns `neighbors` in `ngbr_cell_info`. Each entry includes an identifier plus optional `rsrp` and `rsrq` readings. Tha
ese are surfaced through the metrics API and documented here to ensure discoverability.

## Snapshot Expectations
Every telemetry snapshot produced by the REST client **must** populate the following:

1. LTE metrics listed above
2. NR metrics when available (5G NR capable deployments)
3. Provider, band summary, WAN IP, and connection mode
4. Neighbor metadata when the modem exposes it
5. Temperature tuple `temp (A/M/P)`

These requirements are enforced by contract tests (`tests/unit/test_metrics_docs.py`) to guarantee that new captures remain docume
nted.
