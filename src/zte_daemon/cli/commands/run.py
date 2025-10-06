"""Implementation of the `zte run` command."""
from __future__ import annotations

import click

from zte_daemon.logging.config import configure_logging
from zte_daemon.modem.mock_client import MockModemClient, ModemFixtureError
from zte_daemon.mqtt.mock_broker import MockMQTTBroker


def _derive_device_id(device_host: str) -> str:
    return f"zte-{device_host.replace('.', '-')}-mock"


@click.command(name="run")
@click.option(
    "device_host",
    "--device-host",
    default="192.168.0.1",
    show_default=True,
    help="Local modem address",
)
@click.option(
    "device_pass",
    "--device-pass",
    required=True,
    help="Password used for modem REST authentication",
)
@click.option(
    "log_level",
    "--log",
    type=click.Choice(["debug", "info", "warn", "error"], case_sensitive=False),
    default="info",
    show_default=True,
    help="Log level for stdout and file handlers",
)
@click.option(
    "foreground",
    "--foreground",
    is_flag=True,
    default=False,
    help="Run in foreground (runs in background by default).",
)
@click.option(
    "log_file",
    "--log-file",
    type=click.Path(path_type=str),
    help="Optional log file destination (ensures parent dir exists).",
)
@click.option("mqtt_host", "--mqtt-host", help="Placeholder broker address (stored but not contacted).")
@click.option(
    "mqtt_topic",
    "--mqtt-topic",
    default="zte-modem",
    show_default=False,
    help="Topic used in mock publish [default: zte-modem]",
)
@click.option("mqtt_user", "--mqtt-user", help="MQTT username placeholder.")
@click.option("mqtt_password", "--mqtt-password", help="MQTT password placeholder (never logged).")
def run_command(
    *,
    device_host: str,
    device_pass: str,
    log_level: str,
    foreground: bool,
    log_file: str | None,
    mqtt_host: str | None,
    mqtt_topic: str,
    mqtt_user: str | None,
    mqtt_password: str | None,
) -> dict[str, object]:
    """Run the ZTE modem daemon with mocked MQTT publish loop."""
    del device_pass  # authentication not required for mock flow but accepted for contract compliance
    logger = configure_logging(log_level, log_file)
    logger.info(
        "Starting mocked daemon run",
        extra={"component": "CLI", "context": {"foreground": foreground}},
    )

    modem = MockModemClient()
    try:
        snapshot = modem.load_snapshot()
    except ModemFixtureError as exc:
        raise click.ClickException(str(exc)) from exc

    click.echo("Hello from the ZTE MC888 Ultra mock daemon!")
    click.echo(f"Modem snapshot timestamp: {snapshot.timestamp}")
    click.echo(f"RSRP: {snapshot.rsrp} dBm | Provider: {snapshot.provider}")

    broker = MockMQTTBroker(device_id=_derive_device_id(device_host))
    record = broker.publish(snapshot, topic=mqtt_topic, broker_host=mqtt_host)
    logger.info(
        "Recorded MQTT payload to mock broker",
        extra={
            "component": "MQTTMock",
            "context": {
                "topic": mqtt_topic,
                "broker_host": mqtt_host or "mock-default",
            },
        },
    )
    click.echo("Recorded MQTT payload to mock broker for offline inspection.")

    return {
        "topic": record.topic,
        "payload": record.payload,
        "device_id": broker.device_id,
        "log_file": log_file,
        "mqtt_user": mqtt_user,
    }
