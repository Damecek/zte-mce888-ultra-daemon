# MQTT Contract Overview

The `zte run` daemon exchanges messages following the contract defined in
[`specs/003-we-need-to/contracts/mqtt.md`](../specs/003-we-need-to/contracts/mqtt.md).
Requests use a lowercase root topic (default `zte`) with the pattern
`<root>/<metric>/get` and responses are published on `<root>/<metric>`.

## Request Examples

```text
# Request the current provider value
mosquitto_pub -h 192.168.0.242 -t 'zte/provider/get' -n

# Request the LTE aggregate payload
mosquitto_pub -h 192.168.0.242 -t 'zte/lte/get' -n
```

## Response Examples

```text
# Published by the daemon after the provider request
Topic: zte/provider
Payload: "O2"

# Published by the daemon after the LTE aggregate request
Topic: zte/lte
Payload:
{
  "rsrp1": -92.0,
  "sinr1": 12.5,
  "rsrq": -9.0,
  "pci": 123
}
```

## Delivery Guarantees

* QoS: `0`
* Retain flag: `False`
* Messages are processed sequentially with a reconnect delay of five seconds.

For integration walkthroughs see the Quickstart section in
[`specs/003-we-need-to/quickstart.md`](../specs/003-we-need-to/quickstart.md).
