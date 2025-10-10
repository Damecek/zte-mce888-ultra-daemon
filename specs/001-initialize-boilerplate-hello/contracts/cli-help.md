# CLI Help Contract

Expected `zte --help` top-level snippet:
```
Usage: zte [OPTIONS] COMMAND [ARGS]...

Options:
  --version  Show the version and exit.
  --help     Show this message and exit.

Commands:
  run   Run the ZTE modem daemon with mocked MQTT publish loop.
  read  Read a modem metric from cached telemetry (e.g., RSRP, Provider).
```

Expected `zte run --help` flags:
```
Usage: zte run [OPTIONS]

Options:
  --device-host TEXT        Local modem address [default: 192.168.0.1]
  --device-pass TEXT        Password used for modem REST authentication [required]
  --log [debug|info|warn|error]
                            Log level for stdout and file handlers [default: warn]
  --foreground              Run in foreground (runs in background by default).
  --log-file PATH           Optional log file destination (ensures parent dir exists).
  --mqtt-host TEXT          Placeholder broker address (stored but not contacted).
  --mqtt-topic TEXT         Topic used in mock publish [default: zte-modem].
  --mqtt-user TEXT          MQTT username placeholder.
  --mqtt-password TEXT      MQTT password placeholder (never logged).
  --help                    Show this message and exit.
```

Expected `zte read --help` snippet:
```
Usage: zte read [OPTIONS] METRIC

Arguments:
  METRIC  Metric name (RSRP, Provider)

Options:
  --help  Show this message and exit.
```
