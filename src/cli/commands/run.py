from __future__ import annotations

import asyncio
import signal

import click

from lib.logging_setup import get_logger, logging_options
from lib.options import router_options
from models.daemon_state import DaemonState
from models.mqtt_config import MQTTConfig
from models.router_config import RouterConfig
from pipeline.dispatcher import Dispatcher
from services import zte_client
from services.metrics_aggregator import MetricsAggregator
from services.mqtt_client import MQTTClient


async def _run_daemon(
    *,
    router_host: str,
    router_password: str,
    log_level: str,
    log_file: str | None,
    mqtt_host: str,
    mqtt_port: int,
    mqtt_username: str | None,
    mqtt_password: str | None,
    mqtt_topic: str | None,
    foreground: bool,
) -> None:
    """
    Start and run the ZTE daemon: authenticate to the router, maintain an MQTT connection, and dispatch metric requests until a termination signal is received.
    
    Parameters:
        router_host (str): Hostname or IP address of the ZTE router to connect to.
        router_password (str): Password used to authenticate with the router.
        log_level (str): Logging level name (e.g., "INFO", "DEBUG").
        log_file (str | None): Path to a log file, or None to log to stdout.
        mqtt_host (str): MQTT broker hostname or IP address.
        mqtt_port (int): MQTT broker TCP port.
        mqtt_username (str | None): Username for MQTT authentication, or None if not used.
        mqtt_password (str | None): Password for MQTT authentication, or None if not used.
        mqtt_topic (str): Root MQTT topic used for publishing and subscribing.
        foreground (bool): If true, run in the foreground; otherwise allow background-style operation.
    
    Side effects:
        - Attempts to authenticate and maintain a persistent connection to the router and MQTT broker.
        - Runs an event loop that responds to incoming MQTT messages and records connection failures.
        - Stops only after receiving SIGINT or SIGTERM and performs cleanup (closing router client and MQTT client).
    """
    logger = get_logger(log_level, log_file)
    router_config = RouterConfig(host=router_host, password=router_password)
    # Effective root topic always includes the 'zte' group.
    effective_root = f"{mqtt_topic.strip()}/zte" if mqtt_topic else "zte"
    mqtt_config = MQTTConfig(
        host=mqtt_host,
        port=mqtt_port,
        username=mqtt_username,
        password=mqtt_password,
        root_topic=effective_root,
    )
    state = DaemonState()

    logger.info(
        "Starting ZTE daemon",
        extra={
            "router_host": router_config.host,
            "mqtt_host": mqtt_config.host,
            "mqtt_port": mqtt_config.port,
            "root_topic": mqtt_config.root_topic,
            "foreground": foreground,
        },
    )

    client = zte_client.ZTEClient(router_config.host)
    try:
        client.login(router_config.password)
    except zte_client.ZTEClientError as exc:
        raise click.ClickException(f"Failed to authenticate with router: {exc}") from exc

    aggregator = MetricsAggregator(client)
    mqtt_client = MQTTClient(mqtt_config)
    dispatcher = Dispatcher(
        mqtt_config=mqtt_config,
        metric_reader=aggregator,
        aggregator=aggregator,
        mqtt_client=mqtt_client,
        state=state,
    )
    mqtt_client.set_message_handler(lambda topic, payload: dispatcher.handle_request(topic, payload))

    stop_event = asyncio.Event()
    loop = asyncio.get_running_loop()
    for signame in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(signame, stop_event.set)

    try:
        while not stop_event.is_set():
            try:
                await mqtt_client.connect()
                state.mark_connected()
                # asyncio.wait() requires Tasks/Futures, not bare coroutines
                stop_task = asyncio.create_task(stop_event.wait())
                disconnect_task = asyncio.create_task(mqtt_client.wait_for_disconnect())
                try:
                    await asyncio.wait(
                        [stop_task, disconnect_task],
                        return_when=asyncio.FIRST_COMPLETED,
                    )
                finally:
                    # Ensure we don't leak tasks when loop iteration ends
                    for t in (stop_task, disconnect_task):
                        if not t.done():
                            t.cancel()
            except asyncio.CancelledError:
                raise
            except Exception as exc:  # pragma: no cover - defensive loop
                logger.warning(
                    "MQTT loop error; retrying in %ss",
                    mqtt_config.reconnect_seconds,
                    exc_info=exc,
                )
                state.record_failure()
            finally:
                state.mark_disconnected()
                await mqtt_client.disconnect()
                if not stop_event.is_set():
                    await asyncio.sleep(mqtt_config.reconnect_seconds)
    finally:
        client.close()
        logger.info("Daemon stopped", extra={"failures": state.failures})


@click.command(name="run")
@router_options(default_host="http://192.168.0.1")
@logging_options(help_text="Log level for stdout and file handlers")
@click.option("foreground", "--foreground", is_flag=True, help="Run in foreground (default).")
@click.option("mqtt_host", "--mqtt-host", required=True, help="MQTT broker hostname or IP address.")
@click.option("mqtt_port", "--mqtt-port", default=1883, show_default=True, type=int, help="MQTT broker port")
@click.option("mqtt_username", "--mqtt-username", help="MQTT username if authentication is required.")
@click.option("mqtt_password", "--mqtt-password", help="MQTT password if authentication is required.")
@click.option(
    "mqtt_topic",
    "--mqtt-topic",
    default=None,
    help=("Optional root prefix. Effective request topics are '<root>/zte/...'.\nIf omitted, requests use 'zte/...'."),
)
def run_command(
    router_host: str,
    router_password: str,
    log_level: str,
    log_file: str | None,
    foreground: bool,
    mqtt_host: str,
    mqtt_port: int,
    mqtt_username: str | None,
    mqtt_password: str | None,
    mqtt_topic: str | None,
) -> None:
    """
    Start the ZTE router daemon and run its MQTT-driven event loop.
    
    Parameters:
    	router_host (str): Hostname or IP address of the ZTE router to connect to.
    	router_password (str): Password used to authenticate with the router.
    	log_level (str): Logging verbosity level (e.g., "DEBUG", "INFO").
    	log_file (str | None): Optional path to a log file; if None logs go to stderr.
    	foreground (bool): If True, run in the foreground instead of detaching.
    	mqtt_host (str): MQTT broker hostname or IP address.
    	mqtt_port (int): MQTT broker port.
    	mqtt_username (str | None): Optional username for MQTT authentication.
    	mqtt_password (str | None): Optional password for MQTT authentication.
    	mqtt_topic (str): Root MQTT topic used for publishing and subscribing.
    """

    try:
        asyncio.run(
            _run_daemon(
                router_host=router_host,
                router_password=router_password,
                log_level=log_level,
                log_file=log_file,
                mqtt_host=mqtt_host,
                mqtt_port=mqtt_port,
                mqtt_username=mqtt_username,
                mqtt_password=mqtt_password,
                mqtt_topic=mqtt_topic,
                foreground=foreground,
            )
        )
    except KeyboardInterrupt:  # pragma: no cover - interactive flow
        pass