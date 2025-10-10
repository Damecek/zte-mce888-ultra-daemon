# Quickstart — ZTE Daemon (`zte run`)

## Prerequisites
- Local MQTT broker reachable (e.g., `192.168.0.242`)
- Local modem at `http://192.168.0.1` (adjust as needed)

## Run the daemon
```
uv run zte run \
  --router-host=http://192.168.0.1 \
  --router-password=YOUR_PASSWORD \
  --mqtt-host=192.168.0.242 \
  --mqtt-port=1883 \
  --mqtt-username=USERNAME \
  --mqtt-password=PASSWORD \
  --mqtt-topic=zte \
  --foreground
```

## Request a single metric
```
mosquitto_pub -h 192.168.0.242 -t 'zte/provider/get' -n
```

Expected publish from daemon:
- Topic: `zte/provider`
- Payload (JSON scalar): e.g., `"O2"`

## Request LTE aggregate
```
mosquitto_pub -h 192.168.0.242 -t 'zte/lte/get' -n
```

Expected publish from daemon:
- Topic: `zte/lte`
- Payload (JSON object): LTE metrics per `/docs/metrics.md`.

## Notes
- Topics are lowercased.
- QoS 0, retain false.
- One request is processed at a time.
- Plaintext MQTT only for this feature. TLS to be added later.
