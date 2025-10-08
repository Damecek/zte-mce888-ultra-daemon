"""Implementation of the `zte run` command (flattened src layout)."""

from __future__ import annotations

import click

from lib.logging_setup import get_logger, logging_options
from services import zte_client
from services.modem_mock import MockModemClient, ModemFixtureError
from services.mqtt_mock import MockMQTTBroker


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
@logging_options(help_text="Log level for stdout and file handlers")
@click.option(
    "foreground",
    "--foreground",
    is_flag=True,
    default=False,
    help="Run in foreground (runs in background by default).",
)
@click.option(
    "mqtt_host", "--mqtt-host", help="Placeholder broker address (stored but not contacted)."
)
@click.option(
    "mqtt_topic",
    "--mqtt-topic",
    default="zte-modem",
    show_default=False,
    help="Topic used in mock publish [default: zte-modem]",
)
@click.option("mqtt_user", "--mqtt-user", help="MQTT username placeholder.")
@click.option("mqtt_password", "--mqtt-password", help="MQTT password placeholder (never logged).")
@click.option(
    "rest_test",
    "--rest-test",
    is_flag=True,
    default=False,
    help="Attempt a minimal REST client login + fetch before mock publish (test mode).",
)
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
    rest_test: bool,
) -> dict[str, object]:
    """Run the ZTE modem daemon with mocked MQTT publish loop."""
    logger = get_logger(log_level, log_file)
    device_id = _derive_device_id(device_host)
    logger.info(
        f"Starting mocked daemon run (foreground={foreground}, device_id={device_id})"
    )

    # Optional: exercise REST client in a minimal way for test-mode verification
    if rest_test:
        try:
            client = zte_client.ZTEClient(f"http://{device_host}")
            client.login(device_pass)
            # Lightweight GET against a benign endpoint to verify session
            client.request(
                "/goform/goform_get_cmd_process?isTest=false&cmd=lan_station_list",
                method="GET",
                expects="json",
            )
            logger.info("REST client test-mode fetch succeeded")
        except zte_client.ZTEClientError as exc:
            raise click.ClickException(f"REST test-mode failed: {exc}") from exc

    modem = MockModemClient()
    try:
        snapshot = modem.load_snapshot()
    except ModemFixtureError as exc:
        raise click.ClickException(str(exc)) from exc

    click.echo(f"Modem snapshot timestamp: {snapshot.timestamp}")
    click.echo(f"RSRP: {snapshot.rsrp} dBm | Provider: {snapshot.provider}")

    broker = MockMQTTBroker(device_id=device_id)
    record = broker.publish(snapshot, topic=mqtt_topic, broker_host=mqtt_host)
    logger.info(
        f"Recorded MQTT payload to mock broker (topic={mqtt_topic}, broker={mqtt_host or 'mock-default'})"
    )
    click.echo("Recorded MQTT payload to mock broker for offline inspection.")

    return {
        "topic": record.topic,
        "payload": record.payload,
        "device_id": broker.device_id,
        "log_file": log_file,
        "mqtt_user": mqtt_user,
    }
