# ZTE MC888 Ultra Metrics Catalog

## LTE Metrics
- **rsrp1** – LTE primary cell RSRP (dBm)
- **sinr1** – LTE primary cell SINR (dB)
- **rsrp2** – Secondary cell RSRP (dBm)
- **sinr2** – Secondary cell SINR (dB)
- **rsrp3** – Third cell RSRP (dBm)
- **sinr3** – Third cell SINR (dB)
- **rsrp4** – Fourth cell RSRP (dBm)
- **sinr4** – Fourth cell SINR (dB)
- **rsrq** – LTE signal quality (dB)
- **rssi** – LTE received signal strength indicator (dBm)
- **earfcn** – LTE EARFCN identifier
- **pci** – LTE Physical Cell ID
- **bw** – LTE channel bandwidth description (e.g., `10MHz`)

## NR5G Metrics
- **rsrp1** – NR primary cell RSRP (dBm)
- **rsrp2** – NR secondary cell RSRP (dBm)
- **sinr** – NR SINR (dB)
- **arfcn** – NR ARFCN identifier
- **pci** – NR Physical Cell ID
- **bw** – NR channel bandwidth description (e.g., `10MHz`)

## Provider
- **provider** – Network operator full name reported by the modem UI.

## Cell
- **cell** – Serving cell identifier for the LTE anchor.

## Neighbor Cells
- **neighbors[].id** – Neighbor cell identifier.
- **neighbors[].rsrp** – Neighbor RSRP (dBm).
- **neighbors[].rsrq** – Neighbor RSRQ (dB).

## Connection State
- **connection** – Aggregated connection mode (e.g., `ENDC`).

## Bands
- **bands** – Combined LTE/NR band summary such as `B20(10MHz) + n28(10MHz)`.

## WAN IP
- **wan_ip** – Public WAN IP address assigned to the modem.

## Temperatures
- **temp.a** – Ambient temperature sensor (°C).
- **temp.m** – Modem temperature sensor (°C).
- **temp.p** – Power amplifier temperature sensor (°C).
